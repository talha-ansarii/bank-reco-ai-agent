import requests
from typing import List
from pydantic import BaseModel
from datetime import datetime
import json


# Data model
class Statement(BaseModel):
    date: str
    amount: float
    description: str
    
import pandas as pd
import pandas as pd

import pandas as pd
import json
from dotenv import load_dotenv
import os
load_dotenv()

def extract_transactions(file_path, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    sheet_names = ["Bank statements FY 24-25", "Bank statements FY 25-26"]
    all_data = []

    for sheet in sheet_names:
        # print(f"\nReading sheet: {sheet}")
        
        # Try reading with different skiprows until we find the header
        for skip in range(0, 10):
            df = pd.read_excel(file_path, sheet_name=sheet, skiprows=skip)
            df.columns = [str(col).strip().lower() for col in df.columns]

            # print(f"Trying skiprows={skip}, columns: {df.columns.tolist()}")

            # Heuristic: look for 'tran' and 'remark'
            has_date = any('tran' in col and 'date' in col for col in df.columns)
            has_remark = any('remark' in col for col in df.columns)

            if has_date and has_remark:
                # print(f"✅ Header found at skiprows={skip}")
                break
        else:
            raise ValueError(f"❌ Could not detect correct header in sheet: {sheet}")

        # Get columns using partial matching
        date_col = next((col for col in df.columns if 'tran' in col and 'date' in col), None)
        desc_col = next((col for col in df.columns if 'remark' in col), None)
        withdrawal_col = next((col for col in df.columns if 'withdrawal' in col), None)
        deposit_col = next((col for col in df.columns if 'deposit' in col), None)

        if not all([date_col, desc_col]):
            raise ValueError(f"Required columns missing in sheet: {sheet}")

        # Convert date column to datetime and drop invalid dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df[df[date_col].notna()]

        # Compute amount: deposit - withdrawal
        df['amount'] = df.get(deposit_col, 0).fillna(0) - df.get(withdrawal_col, 0).fillna(0)

        # Select and rename the columns we need
        cleaned = df[[date_col, desc_col, 'amount']].copy()
        cleaned.columns = ['date', 'description', 'amount']

        all_data.append(cleaned)

    # Combine data from all sheets and filter by date
    result = pd.concat(all_data, ignore_index=True)
    result = result[(result['date'] >= start_date) & (result['date'] <= end_date)]
    print(f"✅ Found {len(result)} transactions in the date range.")
    result = result.sort_values('date')
    result['date'] = result['date'].dt.strftime('%Y-%m-%d')
    records = result.to_dict(orient='records')
    return records

# Usage:
# records = extract_transactions("DetailedStatement.xlsx", "2024-06-01", "2024-06-30")

# print("fetching transactions from excel file")
# print(json.dumps(records, indent=4))



pdf_lambda_api = os.getenv("PDF_LAMBDA_API_URL")
pdf_lambda_x_client_key = os.getenv("PDF_LAMBDA_X_CLIENT_KEY")
pdf_lambda_org_id = os.getenv("PDF_LAMBDA_ORG_ID")

def fetch_pdf_statements(file_path: str, start_date: str, end_date: str) -> List[Statement]:
    url = pdf_lambda_api
    headers = {
        'x-client-key': pdf_lambda_x_client_key,
        'Content-Type': 'application/pdf',
        'organization-id': pdf_lambda_org_id
    }

    # Read PDF as binary
    with open(file_path, 'rb') as f:
        payload = f.read()

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    json_data = response.json()

    line_items = json_data.get("line_items", [])
    statements = []

    # Convert string inputs to datetime for comparison
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    for item in line_items:
        date_str = item.get("date")
        try:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            continue

        if not (start <= date_obj <= end):
            continue

        formatted_date = date_obj.strftime("%Y-%m-%d")
        deposit = item.get("deposit", 0.0)
        withdrawal = item.get("withdrawal", 0.0)
        amount = deposit - withdrawal

        description = item.get("description", "No description")

        statements.append({"date" : formatted_date, "amount" : amount, "description" : description})

    return statements

# print("Fetching PDF statements...", json.dumps(fetch_pdf_statements("bank.pdf", "2025-03-30", "2025-04-29"), indent=2))



from dataclasses import dataclass

@dataclass
class Statement:
    date: str
    amount: float
    description: str


rootfi_api_base_url = os.getenv("ROOTFI_API_BASE_URL")
rootfi_api_key = os.getenv("ROOTFI_API_KEY")

def fetch_book_statements(start_date: str, end_date: str, comapny_id: str):
    url = f"{rootfi_api_base_url}/accounting/bank_transactions"
    querystring = {
        "rootfi_company_id[eq]": comapny_id,
        "expand": "account",
        "limit": "100"
    }
    headers = {
        "api_key": rootfi_api_key,
    }

    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    json_data = response.json()

    transactions = json_data.get("data", [])
    statements = []

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    for item in transactions:
        # print("book statement" ,json.dumps(item, indent=2))
        transaction_date = item.get("transaction_date", "")
        if not transaction_date:
            continue

        date_obj = datetime.fromisoformat(transaction_date.replace("Z", ""))
        if not (start <= date_obj <= end):
            continue

        date_str = date_obj.strftime("%Y-%m-%d")
        amount = float(item.get("amount", 0))
        if item.get("debit_or_credit", "").upper() == "DEBIT":
            amount = -amount

        account = item.get("account", {})
        description = account.get("description") or "No description"
        print(description)
        statements.append({
            "date": date_str,
            "amount": amount,
            "description": description
        })

    return statements



# # Print statements in JSON format
# print("Fetching book statements...")
# statements = fetch_book_statements("2024-06-01", "2024-06-30", "18026")
# print(json.dumps(statements, indent=2))



