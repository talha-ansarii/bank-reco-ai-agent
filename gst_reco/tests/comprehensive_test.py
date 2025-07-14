"""
Comprehensive test script for GST Reconciliation with sample data
Tests both GSTR-2A and GSTR-2B formats
"""

import json
import pandas as pd
import os
from gst_reco.main import kickoff_gst_reconciliation

# Sample GSTR-2A JSON data
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
        },
        {
            "cfs": "Y",
            "ctin": "29AABCI2726B1ZY",
            "fldtr1": "11-Apr-25",
            "cfs3b": "Y",
            "invoice_type": "b2b",
            "items": [
                {
                    "inum": "KA1242503DK97450",
                    "val": 2310,
                    "inv_typ": "R",
                    "pos": "29",
                    "idt": "22-03-2025",
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

# Sample GSTR-2B JSON data
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
            "val": 143885,
            "sgst": 0,
            "rev": "N",
            "itcavl": "Y",
            "txval": 121936,
            "typ": "R",
            "cgst": 0,
            "inum": "AL-2425-0038",
            "rsn": "",
            "cess": 0,
            "igst": 21948.48,
            "dt": "07-03-2025",
            "imsStatus": "N",
            "pos": "29",
            "trdnm": "APPROLABS PRIVATE LIMITED",
            "supfildt": "10-04-2025",
            "supprd": "032025",
            "ctin": "33AAUCA1846M1Z8",
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
        },
        {
            "val": 2310,
            "sgst": 55,
            "rev": "N",
            "itcavl": "Y",
            "txval": 2200,
            "typ": "R",
            "cgst": 55,
            "inum": "KA1242503DK97450",
            "rsn": "",
            "cess": 0,
            "igst": 0,
            "dt": "22-03-2025",
            "imsStatus": "N",
            "pos": "29",
            "trdnm": "INTERGLOBE AVIATION LIMITED",
            "supfildt": "11-04-2025",
            "supprd": "032025",
            "ctin": "29AABCI2726B1ZY",
            "invoice_type": "b2b"
        }
    ],
    "gendt": "14-04-2025",
    "gstin": "29AAUFN1717D1Z3",
    "version": "1.0"
}


def create_sample_excel_file():
    """Create a sample Excel file matching the screenshot format"""

    # Sample Books data matching the Excel screenshot format
    books_data = [
        {
            'GSTIN': '29ETLPB1739K1ZB',
            'Name': 'Neo Fasteners',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': '27',
            'Voucher No': '550',
            'Voucher Ref. Date': '21-03-2025',
            'Taxable Value': 2705.00,
            'IGST': '-',
            'CGST': 243.45,
            'SGST': 243.45,
            'Source': 'SGST - 9%'
        },
        {
            'GSTIN': '24ABKCS2033B1ZV',
            'Name': 'Sandbox Financial Technologies',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': '11129',
            'Voucher No': '551',
            'Voucher Ref. Date': '13-01-2025',
            'Taxable Value': 846.61,
            'IGST': 152.39,
            'CGST': '-',
            'SGST': '-',
            'Source': 'IGST - 18%'
        },
        {
            'GSTIN': '24ABKCS2033B1ZV',
            'Name': 'Sandbox Financial Technologies',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': '11652',
            'Voucher No': '552',
            'Voucher Ref. Date': '13-02-2025',
            'Taxable Value': 2287.29,
            'IGST': 411.71,
            'CGST': '-',
            'SGST': '-',
            'Source': 'IGST - 18%'
        },
        {
            'GSTIN': '33AAUCA1846M1Z8',
            'Name': 'Approlabs Private Limited',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': 'AL-2425-0038',
            'Voucher No': '553',
            'Voucher Ref. Date': '07-03-2025',
            'Taxable Value': 121936.00,
            'IGST': 21948.48,
            'CGST': '-',
            'SGST': '-',
            'Source': 'IGST - 18%'
        },
        {
            'GSTIN': '29AABCI2726B1ZY',
            'Name': 'Interglobe Aviation Limited',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': 'KA1242503DK97450',
            'Voucher No': '554',
            'Voucher Ref. Date': '22-03-2025',
            'Taxable Value': 2200.00,
            'IGST': '-',
            'CGST': 55.00,
            'SGST': 55.00,
            'Source': 'CGST/SGST - 5%'
        },
        {
            'GSTIN': '29AAMCB6502D1ZS',
            'Name': 'BKC PICMYCHIP TECH SERVICES PRIVATE LIMITED',
            'Invoice Type': 'Invoice',
            'Voucher Ref. No.': 'INV-000171',
            'Voucher No': '555',
            'Voucher Ref. Date': '25-03-2025',
            'Taxable Value': 3502.00,
            'IGST': '-',
            'CGST': 315.18,
            'SGST': 315.18,
            'Source': 'SGST - 9%'
        }
    ]

    # Create DataFrame
    df = pd.DataFrame(books_data)

    # Save to Excel with proper sheet name
    excel_file_path = "sample_books_data.xlsx"
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Book ITC', index=False)

    print(f"Created sample Excel file: {excel_file_path}")
    return excel_file_path


def test_gstr_2a_reconciliation():
    """Test GST reconciliation with GSTR-2A data"""
    print("\n" + "="*60)
    print("TESTING GSTR-2A RECONCILIATION")
    print("="*60)

    # Create sample Excel file
    books_file_path = create_sample_excel_file()

    try:
        # Run reconciliation with GSTR-2A data
        results = kickoff_gst_reconciliation(
            gstr_json=sample_gstr_2a_data,
            books_file_path=books_file_path,
            company_id="TEST_GSTR2A",
            sheet_name="Book ITC"
        )

        print_results(results, "GSTR-2A")

    except Exception as e:
        print(f"GSTR-2A Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_gstr_2b_reconciliation():
    """Test GST reconciliation with GSTR-2B data"""
    print("\n" + "="*60)
    print("TESTING GSTR-2B RECONCILIATION")
    print("="*60)

    # Create sample Excel file
    books_file_path = create_sample_excel_file()

    try:
        # Run reconciliation with GSTR-2B data
        results = kickoff_gst_reconciliation(
            gstr_json=sample_gstr_2b_data,
            books_file_path=books_file_path,
            company_id="TEST_GSTR2B",
            sheet_name="Book ITC"
        )

        print_results(results, "GSTR-2B")

    except Exception as e:
        print(f"GSTR-2B Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def print_results(results, test_type):
    """Print reconciliation results in a formatted manner"""
    print(f"\n{test_type} Reconciliation Results:")
    print(f"Status: {results.get('status')}")

    if results.get('status') == 'success':
        summary = results.get('summary', {})
        print(f"\n📊 SUMMARY:")
        print(f"   Total Records: {summary.get('total_records', 0)}")
        print(f"   ✅ Matched Records: {summary.get('matched_count', 0)}")
        print(
            f"   ⚠️  Partial Matches: {summary.get('partial_match_count', 0)}")
        print(f"   ❌ GSTR Only Records: {summary.get('gstr_only_count', 0)}")
        print(f"   🟡 Books Only Records: {summary.get('books_only_count', 0)}")
        print(f"   📈 Match Percentage: {summary.get('match_percentage', 0)}%")
        print(
            f"   💰 Matched Amount (GSTR): ₹{summary.get('matched_amount_gstr', 0):,.2f}")
        print(
            f"   💰 Matched Amount (Books): ₹{summary.get('matched_amount_books', 0):,.2f}")
        print(
            f"   💰 Amount Difference: ₹{summary.get('amount_difference', 0):,.2f}")

        # Print some sample matched records
        matched_records = results.get('matched_records', [])
        if matched_records:
            print(f"\n✅ Sample Matched Records:")
            for i, record in enumerate(matched_records[:3]):  # Show first 3
                print(f"   {i+1}. GSTIN: {record.get('supplier_gstin')}")
                print(
                    f"      Invoice: {record.get('invoice_no_gstr')} ↔ {record.get('invoice_no_books')}")
                print(
                    f"      Amount: ₹{record.get('taxable_value_gstr')} ↔ ₹{record.get('taxable_value_books')}")
                print(f"      Match Score: {record.get('match_score')}")

        # Print unmatched records
        gstr_only = results.get('gstr_only_records', [])
        if gstr_only:
            print(f"\n❌ GSTR Only Records ({len(gstr_only)}):")
            for i, record in enumerate(gstr_only[:3]):  # Show first 3
                print(f"   {i+1}. GSTIN: {record.get('supplier_gstin')}")
                print(f"      Invoice: {record.get('invoice_no')}")
                print(f"      Amount: ₹{record.get('taxable_value')}")

        books_only = results.get('books_only_records', [])
        if books_only:
            print(f"\n🟡 Books Only Records ({len(books_only)}):")
            for i, record in enumerate(books_only[:3]):  # Show first 3
                print(f"   {i+1}. GSTIN: {record.get('supplier_gstin')}")
                print(f"      Invoice: {record.get('invoice_no')}")
                print(f"      Amount: ₹{record.get('taxable_value')}")

        # Print report paths
        report_paths = results.get('report_paths', {})
        if report_paths:
            print(f"\n📁 Generated Reports:")
            for report_type, path in report_paths.items():
                print(f"   - {report_type}: {path}")
    else:
        print(f"❌ Error: {results.get('message')}")


def run_comprehensive_test():
    """Run comprehensive tests for both GSTR-2A and GSTR-2B"""
    print("🚀 Starting Comprehensive GST Reconciliation Tests")
    print("="*70)

    # Test GSTR-2A
    test_gstr_2a_reconciliation()

    # Test GSTR-2B
    test_gstr_2b_reconciliation()

    print("\n" + "="*70)
    print("✅ Comprehensive Testing Completed!")
    print("="*70)


if __name__ == "__main__":
    run_comprehensive_test()
