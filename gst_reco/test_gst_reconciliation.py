"""
Sample test file for GST Reconciliation
"""

import json
import os
from gst_reco.main import kickoff_gst_reconciliation

# Sample GSTR-2A/2B JSON data
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
            },
            {
                "cfs": "Y",
                "ctin": "24ABKCS2033B1ZV",
                "fldtr1": "10-Mar-25",
                "cfs3b": "Y",
                "invoice_type": "b2b",
                "items": [
                    {
                        "inum": "11652",
                        "val": 2699,
                        "inv_typ": "R",
                        "pos": "29",
                        "idt": "13-02-2025",
                        "rchrg": "N"
                    }
                ]
            },
            {
                "cfs": "Y",
                "ctin": "33AAUCA1846M1Z8",
                "fldtr1": "10-Apr-25",
                "cfs3b": "Y",
                "invoice_type": "b2b",
                "items": [
                    {
                        "inum": "AL-2425-0038",
                        "val": 143885,
                        "inv_typ": "R",
                        "pos": "29",
                        "idt": "07-03-2025",
                        "rchrg": "N"
                    }
                ]
            }
        ]
    }
}


def test_gst_reconciliation():
    """Test the GST reconciliation functionality"""

    # Note: This test requires a sample Excel file with Books data
    # Create a sample Excel file path (you would need to create this file)
    books_file_path = r"C:\Users\talha\Downloads\ITC Reconciliation - FINAL (APR-FEB).xlsx"

    # Check if sample file exists
    if not os.path.exists(books_file_path):
        print("Sample Excel file not found. Please create a sample file with Books data.")
        return

    try:
        # Run reconciliation
        results = kickoff_gst_reconciliation(
            gstr_json=sample_gstr_data,
            books_file_path=books_file_path,
            company_id="TEST_COMPANY",
            sheet_name="Book ITC"
        )

        # Print results
        print("GST Reconciliation Results:")
        print(f"Status: {results.get('status')}")

        if results.get('status') == 'success':
            summary = results.get('summary', {})
            print(f"\nSummary:")
            print(f"Total Records: {summary.get('total_records', 0)}")
            print(f"Matched Records: {summary.get('matched_count', 0)}")
            print(f"Match Percentage: {summary.get('match_percentage', 0)}%")
            print(f"GSTR Only Records: {summary.get('gstr_only_count', 0)}")
            print(f"Books Only Records: {summary.get('books_only_count', 0)}")

            # Print report paths
            report_paths = results.get('report_paths', {})
            print(f"\nGenerated Reports:")
            for report_type, path in report_paths.items():
                print(f"- {report_type}: {path}")
        else:
            print(f"Error: {results.get('message')}")

    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    test_gst_reconciliation()
