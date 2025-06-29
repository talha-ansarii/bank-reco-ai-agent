"""
API Test Script for GST Reconciliation
Tests the FastAPI endpoints with sample data
"""

import requests
import json
import os
from gst_reco.create_sample_data import save_sample_excel

# Sample GSTR-2A data (matching the comprehensive test)
sample_gstr_2a_data = {
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
                },
                {
                    "inum": "11652",
                    "val": 2699,
                    "inv_typ": "R",
                    "pos": "29",
                    "idt": "13-02-2025",
                    "rchrg": "N"
                }
            ]
        }
    ]
}

# Sample GSTR-2B data (matching the comprehensive test)
sample_gstr_2b_data = {
    "itcsumm": {
        "itcavl": {
            "othersup": {},
            "nonrevsup": {
                "sgst": 55,
                "cgst": 55,
                "cess": 0,
                "igst": 36402.87,
                "b2b": {
                    "sgst": 55,
                    "txval": 204438.19,
                    "cgst": 55,
                    "cess": 0,
                    "igst": 36402.87
                }
            }
        }
    },
    "rtnprd": "032025",
    "docdata": [
        {
            "val": 2699,
            "sgst": 0,
            "rev": "N",
            "itcavl": "Y",
            "txval": 2287.29,
            "typ": "R",
            "cgst": 0,
            "inum": "11652",
            "rsn": "",
            "cess": 0,
            "igst": 411.71,
            "dt": "13-02-2025",
            "imsStatus": "N",
            "pos": "29",
            "trdnm": "SANDBOX FINANCIAL TECHNOLOGIES PRIVATE LIMITED",
            "supfildt": "10-03-2025",
            "supprd": "022025",
            "ctin": "24ABKCS2033B1ZV",
            "invoice_type": "b2b"
        },
        {
            "val": 999,
            "sgst": 0,
            "rev": "N",
            "itcavl": "Y",
            "txval": 846.61,
            "typ": "R",
            "cgst": 0,
            "inum": "11129",
            "rsn": "",
            "cess": 0,
            "igst": 152.39,
            "dt": "13-01-2025",
            "imsStatus": "N",
            "pos": "29",
            "trdnm": "SANDBOX FINANCIAL TECHNOLOGIES PRIVATE LIMITED",
            "supfildt": "10-02-2025",
            "supprd": "012025",
            "ctin": "24ABKCS2033B1ZV",
            "invoice_type": "b2b"
        }
    ],
    "gendt": "14-04-2025",
    "gstin": "29AAUFN1717D1Z3",
    "version": "1.0"
}


def test_api_endpoints():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"

    print("🚀 Testing GST Reconciliation API Endpoints")
    print("="*60)

    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            data = response.json()
            print(f"   API Version: {data.get('version')}")
            print(f"   Endpoints: {list(data.get('endpoints', {}).keys())}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")

    print("\n📋 API Test Instructions:")
    print("="*60)

    # Create sample Excel file for testing
    excel_file_path = save_sample_excel()
    print(f"📁 Sample Excel file created: {excel_file_path}")

    # Generate curl commands for testing
    print("\n🔧 CURL Commands for Testing:")
    print("-"*40)

    print("\n1. Test GSTR-2A Reconciliation:")
    gstr_2a_json = json.dumps(sample_gstr_2a_data).replace('"', '\\"')
    curl_2a = f'''curl -X POST "{base_url}/gst-reconcile?company_id=TEST_COMPANY_2A&sheet_name=Book%20ITC" \\
  -F "books_file=@{excel_file_path}" \\
  -F "gstr_data=\\"{gstr_2a_json}\\""'''
    print(curl_2a)

    print("\n2. Test GSTR-2B Reconciliation:")
    gstr_2b_json = json.dumps(sample_gstr_2b_data).replace('"', '\\"')
    curl_2b = f'''curl -X POST "{base_url}/gst-reconcile?company_id=TEST_COMPANY_2B&sheet_name=Book%20ITC" \\
  -F "books_file=@{excel_file_path}" \\
  -F "gstr_data=\\"{gstr_2b_json}\\""'''
    print(curl_2b)

    print("\n📊 Python Test Code:")
    print("-"*40)
    print("""
import requests

# Test with Python requests
with open('sample_books_data.xlsx', 'rb') as f:
    files = {'books_file': f}
    data = {
        'gstr_data': json.dumps(sample_gstr_2a_data)
    }
    params = {
        'company_id': 'TEST_COMPANY',
        'sheet_name': 'Book ITC'
    }
    
    response = requests.post(
        'http://localhost:8000/gst-reconcile',
        files=files,
        data=data,
        params=params
    )
    
    print(response.json())
    """)

    print("\n💡 Tips:")
    print("-"*40)
    print("1. Start the server with: uvicorn app:app --reload")
    print("2. Access API docs at: http://localhost:8000/docs")
    print("3. Use the sample Excel file created above")
    print("4. Check the 'reports' folder for generated output files")

    print(f"\n📁 Sample files created:")
    print(f"   - Excel file: {excel_file_path}")
    print(f"   - Contains sample Books data matching GSTR records")


def test_with_requests():
    """Test using Python requests library"""
    base_url = "http://localhost:8000"

    # Create sample Excel file
    excel_file_path = save_sample_excel()

    print("\n🧪 Testing with Python Requests:")
    print("="*50)

    try:
        with open(excel_file_path, 'rb') as f:
            files = {'books_file': f}
            data = {
                'gstr_data': json.dumps(sample_gstr_2a_data)
            }
            params = {
                'company_id': 'API_TEST_COMPANY',
                'sheet_name': 'Book ITC',
                'fuzzy_threshold': 85,
                'date_tolerance': 2,
                'amount_tolerance': 5.0
            }

            response = requests.post(
                f'{base_url}/gst-reconcile',
                files=files,
                data=data,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ API Test Successful!")
                result = response.json()

                summary = result.get('results', {}).get('summary', {})
                print(f"📊 Results Summary:")
                print(f"   Total Records: {summary.get('total_records', 0)}")
                print(f"   Matched: {summary.get('matched_count', 0)}")
                print(f"   Match %: {summary.get('match_percentage', 0)}%")

                report_paths = result.get(
                    'results', {}).get('report_paths', {})
                if report_paths:
                    print(f"📁 Reports Generated:")
                    for report_type, path in report_paths.items():
                        print(f"   - {report_type}: {path}")
            else:
                print(f"❌ API Test Failed: {response.status_code}")
                print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running")
        print("   Start with: uvicorn app:app --reload")
    except Exception as e:
        print(f"❌ API Test Error: {str(e)}")


if __name__ == "__main__":
    # Test API endpoints info
    test_api_endpoints()

    # Test with actual requests (if server is running)
    try:
        test_with_requests()
    except Exception as e:
        print(f"\n⚠️  Requests test skipped: {str(e)}")
        print("   Start the server first: uvicorn app:app --reload")
