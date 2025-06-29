"""
API Test Script for GST Reconciliation
"""

import requests
import json
import os

# Test data
sample_gstr_data = {
    "status": 200,
    "message": "Successfully retrieved data",
    "data": {
        "fp": "012025",
        "gstin": "29AAUFN1717D1Z3",
        "list": [
            {
                "cfs": "Y",
                "ctin": "24ABKCS2033B1ZV",
                "fldtr1": "10-Feb-25",
                "cfs3b": "Y",
                "invoice_type": "b2b",
                "items": [
                    {
                        "inum": "11129",
                        "val": 999,
                        "inv_typ": "R",
                        "pos": "29",
                        "idt": "13-01-2025",
                        "rchrg": "N"
                    }
                ]
            }
        ]
    }
}


def test_gst_api():
    """Test the GST reconciliation API"""

    # API endpoint
    url = "http://localhost:8000/gst-reconcile"

    # Parameters
    params = {
        "company_id": "TEST_COMPANY_123",
        "sheet_name": "Book ITC",
        "fuzzy_threshold": 85,
        "date_tolerance": 2,
        "amount_tolerance": 5.0
    }

    # Note: You would need a real Excel file for this test
    # For now, this is just a structure demonstration

    print("GST Reconciliation API Test Structure")
    print("=" * 50)
    print(f"Endpoint: {url}")
    print(f"Parameters: {params}")
    print(
        f"GSTR Data Sample: {json.dumps(sample_gstr_data, indent=2)[:200]}...")
    print("\nTo test the actual API:")
    print("1. Start the FastAPI server: uvicorn app:app --reload")
    print("2. Create a sample Excel file with Books data")
    print("3. Use curl or a tool like Postman to test the endpoint")

    # Example curl command
    curl_command = f'''
curl -X POST "{url}?company_id=TEST_COMPANY&sheet_name=Book%20ITC" \\
  -F "books_file=@sample_books.xlsx" \\
  -F "gstr_data='{json.dumps(sample_gstr_data).replace("'", "\\'")}'\"
    '''

    print(f"\nExample curl command:")
    print(curl_command)


if __name__ == "__main__":
    test_gst_api()
