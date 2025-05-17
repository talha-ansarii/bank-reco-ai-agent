import requests
from typing import List
from pydantic import BaseModel
from datetime import datetime
import json

import io

# Data model
class Statement(BaseModel):
    date: str
    amount: float
    description: str

def fetch_pdf_statements(file_path: str, start_date: str, end_date: str) -> List[Statement]:
    url = "https://6pbzobe3yho3frsbfkd4qa6oke0vrozh.lambda-url.ap-south-1.on.aws/"
    headers = {
        'x-client-key': '559ff8e1f03fa29f665ff93f24070f9b461f70ae7ba5c52ac1c728fc885b92d4',
        'Content-Type': 'application/pdf',
        'organization-id': '48f583a0-4836-4941-a6f5-60cda52d3fa1'
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

        statements.append(Statement(date=formatted_date, amount=amount, description=description))

    return statements







def fetch_book_statements(start_date: str, end_date: str, comapny_id: str) -> List[Statement]:
    url = "https://api.rootfi.dev/v3/accounting/bank_transactions"
    querystring = {
        "rootfi_company_id[eq]": "18026",
        "expand": "account",
        "limit": "100"  # Increase limit if needed
    }
    headers = {
        "api_key": "230ac019-3676-4d99-ad4d-8f836b80ba1d"
    }

    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    json_data = response.json()

    transactions = json_data.get("data", [])
    statements = []

    # Convert string inputs to datetime for comparison
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    for item in transactions:
        transaction_date = item.get("transaction_date", "")
        if not transaction_date:
            continue

        # Convert and filter by date range
        date_obj = datetime.fromisoformat(transaction_date.replace("Z", ""))
        if not (start <= date_obj <= end):
            continue

        date_str = date_obj.strftime("%Y-%m-%d")
        amount = float(item.get("amount", 0))
        if item.get("debit_or_credit", "").upper() == "DEBIT":
            amount = -amount

        account = item.get("account", {})
        description = account.get("description") or account.get("name", "No description")

        statements.append(Statement(date=date_str, amount=amount, description=description))

    return statements



