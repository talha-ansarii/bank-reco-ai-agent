#!/usr/bin/env python
import datetime
import time
import json
from typing import List, Dict, Tuple
from pydantic import BaseModel
from dotenv import load_dotenv
from collections import defaultdict
from difflib import SequenceMatcher

from crewai.flow import Flow, listen, start
from crews.compare_statements.compare_statements import CompareStatements
from utils import fetch_book_statements, extract_transactions , fetch_pdf_statements
load_dotenv()

# --- Data Models ---


class Statement(BaseModel):
    date: str
    amount: float
    description: str


class BankRecoState(BaseModel):
    bank_statements: List[Statement] = []
    book_statements: List[Statement] = []
    bank_matched: List[Statement] = []
    book_matched: List[Statement] = []
    start_date: str = ""
    end_date: str = ""
    company_id: str = ""
    file_path: str = ""

# --- Helper Functions ---


def build_book_index(book_statements: List[Statement]) -> Dict[Tuple[float, str], List[Statement]]:
    index = defaultdict(list)
    for b in book_statements:
        date = datetime.datetime.strptime(b["date"], "%Y-%m-%d")
        for delta in range(-3, 4):  # ±3 days
            nearby_date = (date + datetime.timedelta(days=delta)
                           ).strftime("%Y-%m-%d")
            index[(b["amount"], nearby_date)].append(b)
    return index


def is_similar(desc1: str, desc2: str) -> bool:
    return SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio() > 0.85

# --- Flow Class ---


class BankReco(Flow[BankRecoState]):
    def __init__(self, start_date: str, end_date: str, company_id: str, file_path: str):
        super().__init__(BankRecoState())
        self.state.start_date = start_date
        self.state.end_date = end_date
        self.state.company_id = company_id
        self.state.file_path = file_path

        
    @start()
    def load_statements(self):
        print("🚀 Loading bank and book statements")
        start_date = self.state.start_date
        end_date = self.state.end_date
        company_id = self.state.company_id
        file_path = self.state.file_path
        
        #chech if file_path is pdf or xlsx
        if file_path.endswith(".pdf"):
            print("📄 Loading bank statements from PDF")
            bank_statements = fetch_pdf_statements(file_path, start_date, end_date)
            print(f"Bank statements: {json.dumps(bank_statements, indent=2)}")
        elif file_path.endswith(".xlsx"):
            print("📄 Loading bank statements from XLSX")
            bank_statements = extract_transactions(file_path, start_date, end_date)
        else:
            raise ValueError("Unsupported file format. Please provide a PDF or XLSX file.")
        
        # Fetch book statements from API
        book_statements =  fetch_book_statements(start_date, end_date, company_id)
        
        print(f"Bank statemensts: {json.dumps(bank_statements, indent=2)}")
        print(f"Book statemensts: {json.dumps(book_statements, indent=2)}")
        self.state.bank_statements = bank_statements
        self.state.book_statements = book_statements
        print(f"📄 Loaded {len(self.state.bank_statements)} bank statements")
        print(
            f"📘 Loaded {len(self.state.book_statements)} book statements")


    @listen(load_statements)
    def match_statements(self):
        print("🔍 Matching statements...")

        matched_bank = []
        matched_book = []
        matched_book_ids = set()
        verification_needed = []  # Pairs that need LLM verification

        book_index = build_book_index(self.state.book_statements)

        # First pass: fast matching and collecting pairs for LLM verification
        print("🔄 First pass: Fast matching...")
        for bs in self.state.bank_statements:
            candidates = book_index.get((bs["amount"], bs["date"]), [])
            for bk in candidates:
                if id(bk) in matched_book_ids:
                    continue

                # Fast fuzzy match
                if is_similar(bs["description"], bk["description"]):
                # if False:
                    matched_bank.append(bs)
                    matched_book.append(bk)
                    matched_book_ids.add(id(bk))
                    print(
                        "✅ Fast Matched: " + bs["description"] + " ↔  " + bk["description"])
                    break  # Move to next bank statement
                else:
                    # Add to verification queue if fast match fails
                    verification_needed.append((bs, bk))

        print(f"✅ Fast matched: {len(matched_bank)} entries")
        print(f"🔍 Need verification: {len(verification_needed)} pairs")

        # Second pass: process LLM verifications in batches
        if verification_needed:
            print("🧠 Second pass: Batch LLM verification...")

            # Process in batches to reduce API calls
            batch_size = 100  # Adjust based on LLM context window and rate limits
            for i in range(0, len(verification_needed), batch_size):
                batch = verification_needed[i:i+batch_size]

                # Create batch for LLM processing
                batch_inputs = []
                for idx, (bs, bk) in enumerate(batch):
                    batch_inputs.append({
                        "id": idx,
                        "bank_transaction_description": bs["description"],
                        "book_transaction_description": bk["description"],
                    })

                # Send batch to LLM
                print(
                    f"🧠 Processing batch {i//batch_size + 1}/{(len(verification_needed) + batch_size - 1)//batch_size}...")                # Create combined input for batch processing
                batch_input = {
                    "transactions": batch_inputs
                }

                # Call LLM with the batch, explicitly specifying the batch_match_task
                output = CompareStatements().crew().kickoff(
                    inputs=batch_input)

                # Process batch results
                matches = output["matches"]
                print(f"🧠 Batch results: {len(matches)} matches <> {matches}")
                for match in matches:
                    if not match.matched:
                        continue

                    idx = match.id
                    if idx is None or not (0 <= idx < len(batch)):
                        continue

                    bs, bk = batch[idx]

                    if id(bk) in matched_book_ids:
                        continue  # Already matched

                    matched_bank.append(bs)
                    matched_book.append(bk)
                    matched_book_ids.add(id(bk))
                    print("🧠 LLM Batch Matched:" + bs["description"] + " ↔ " + bk.description)


        self.state.bank_matched = matched_bank
        self.state.book_matched = matched_book
        print(f"✔️ Total matched entries: {len(matched_bank)}")

    @listen(match_statements)
    async def save_results(self):
        print("💾 Saving results...")

        matched_bank_set = set((b.date, b.amount, b.description)
                               for b in self.state.bank_matched)
        matched_book_set = set((b["date"], b["amount"], b["description"])
                               for b in self.state.book_matched)
        print(f"Length of matched bank set: {len(matched_bank_set)}")
        print(f"Length of matched book set: {len(matched_book_set)}")
        unmatched_bank = [
            b for b in self.state.bank_statements
            if (b["date"], b["amount"], b["description"]) not in matched_bank_set
        ]
        unmatched_book = [
            b for b in self.state.book_statements
            if (b["date"], b["amount"], b["description"]) not in matched_book_set
        ]
        print(f"Length of unmatched bank: {len(unmatched_bank)}")
        print(f"Length of unmatched book: {len(unmatched_book)}")

        with open("./matched_statements.txt", "w", encoding="utf-8") as f:
            for bank, book in zip(self.state.bank_matched, self.state.book_matched):
                f.write(f"BANK: {bank.model_dump()}\n")
                f.write(f"BOOK: {book.model_dump()}\n")
                f.write("----\n")

        with open("./unmatched_bank.txt", "w", encoding="utf-8") as f:
            for bank in unmatched_bank:
                f.write(f"{json.dumps(bank , indent=4)}\n")

        with open("./unmatched_book.txt", "w", encoding="utf-8") as f:
            for book in unmatched_book:
                f.write(f"{json.dumps(book , indent=4)}\n")

        print(f"📁 Matched entries saved to matched_statements.txt")
        print(f"📁 Unmatched bank entries saved to unmatched_bank.txt")
        print(f"📁 Unmatched book entries saved to unmatched_book.txt")
        
        
        
    def get_results(self) -> Dict[str, List[Dict]]:
        matched_bank_set = set((b.date, b.amount, b.description)
                            for b in self.state.bank_matched)
        matched_book_set = set((b["date"], b["amount"], b["description"])
                            for b in self.state.book_matched)

        unmatched_bank = [
            b for b in self.state.bank_statements
            if (b["date"], b["amount"], b["description"]) not in matched_bank_set
        ]
        unmatched_book = [
            b for b in self.state.book_statements
            if (b["date"], b["amount"], b["description"]) not in matched_book_set
        ]

        return {
            "matched": [
                {
                    "bank": bank.model_dump(),
                    "book": book.model_dump()
                }
                for bank, book in zip(self.state.bank_matched, self.state.book_matched)
            ],
            "unmatched_bank": unmatched_bank,
            "unmatched_book": unmatched_book
        }


# --- Entry Points ---

def kickoff(file_path: str, start_date: str, end_date: str, company_id: str) -> Dict:
    start_time = time.time()
    flow = BankReco(file_path=file_path, start_date=start_date, end_date=end_date, company_id=company_id)
    flow.kickoff()  
    print(f"⏱️ Total time: {time.time() - start_time:.2f}s")
    return flow.get_results()


def plot():
    flow = BankReco()
    flow.plot()


if __name__ == "__main__":
   result = kickoff("bank.pdf", "2025-03-30", "2025-04-29", "18119")
   print("------------------------------------------")
   print(f"Matched: {result['matched']}")
   print(f"Unmatched Bank: {result['unmatched_bank']}")
   print(f"Unmatched Book: {result['unmatched_book']}")
    