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

def fetch_book_statements(start_date: str, end_date: str) -> List[Statement]:
    url = "https://api.rootfi.dev/v3/accounting/bank_transactions"
    querystring = {
        "rootfi_company_id[eq]": "18119",
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


# Example usage
book_statements = fetch_book_statements("2023-03-30", "2023-04-01")
print(book_statements)
