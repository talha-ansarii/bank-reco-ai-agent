# GST Input vs. Books Reconciliation Agent

## Overview

This module provides automated GST Input Tax Credit (ITC) reconciliation between GSTR-2A/GSTR-2B data and Books of Accounts (Purchase Register). It's specifically designed for Indian GST compliance requirements.

## Features

### ✅ Data Processing

- **GSTR-2A/2B JSON Processing**: Extracts and normalizes data from GST portal JSON
- **Books of Accounts Excel Processing**: Reads and processes purchase register data
- **Data Cleaning**: Standardizes formats for GSTINs, invoice numbers, dates, and amounts
- **Data Validation**: Identifies and reports data quality issues

### ✅ Advanced Matching Logic

- **Multi-criteria Matching**: Uses weighted scoring across multiple fields
- **Fuzzy Matching**: Handles variations in invoice numbers using similarity algorithms
- **Date Tolerance**: Allows configurable date range matching (±2 days by default)
- **Amount Tolerance**: Handles minor amount differences (±₹5 by default)

### ✅ Comprehensive Categorization

- **✅ Matched**: Perfect matches between GSTR and Books
- **⚠️ Partial Matches**: Records with some discrepancies requiring review
- **❌ GSTR Only**: Records in GSTR-2A/2B but missing from Books
- **🟡 Books Only**: Records in Books but missing from GSTR-2A/2B

### ✅ Detailed Reporting

- **Detailed Reconciliation Report**: Complete match analysis with scores
- **Summary Report**: High-level statistics and key metrics
- **Unmatched Records Reports**: Separate reports for GSTR-only and Books-only records
- **Partial Matches Report**: Items requiring manual verification
- **JSON Export**: Machine-readable format for further processing

## API Endpoints

### POST `/gst-reconcile`

Performs GST reconciliation between GSTR data and Books of Accounts.

**Parameters:**

- `books_file` (File): Excel file containing Books of Accounts data
- `gstr_data` (Form): JSON string containing GSTR-2A/2B data
- `company_id` (Query): Company identifier
- `sheet_name` (Query, optional): Excel sheet name (default: "Book ITC")
- `fuzzy_threshold` (Query, optional): Fuzzy matching threshold 0-100 (default: 85)
- `date_tolerance` (Query, optional): Date tolerance in days (default: 2)
- `amount_tolerance` (Query, optional): Amount tolerance in rupees (default: 5.0)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/gst-reconcile?company_id=ABC123&sheet_name=Book%20ITC" \
  -F "books_file=@books_data.xlsx" \
  -F "gstr_data={\"status\":200,\"data\":{\"list\":[...]}}"
```

**Response:**

```json
{
  "message": "GST reconciliation completed successfully.",
  "results": {
    "status": "success",
    "summary": {
      "total_records": 100,
      "matched_count": 85,
      "match_percentage": 85.0,
      "gstr_only_count": 10,
      "books_only_count": 5
    },
    "report_paths": {
      "detailed_report": "reports/ABC123_gst_reconciliation_detailed_20250630_143022.csv",
      "summary_report": "reports/ABC123_gst_reconciliation_summary_20250630_143022.csv"
    }
  }
}
```

## Data Formats

### GSTR-2A/2B JSON Format

```json
{
  "status": 200,
  "data": {
    "fp": "012025",
    "gstin": "29AAUFN1717D1Z3",
    "list": [
      {
        "ctin": "24ABKCS2033B1ZV",
        "invoice_type": "b2b",
        "items": [
          {
            "inum": "11129",
            "val": 999,
            "idt": "13-01-2025"
          }
        ]
      }
    ]
  }
}
```

### Books of Accounts Excel Format

Expected columns in "Book ITC" sheet:

- `GSTIN` or `Supplier GSTIN`
- `Invoice No` or `Voucher Ref. No.`
- `Invoice Date` or `Voucher Ref. Date`
- `Taxable Value`
- `IGST`, `CGST`, `SGST` (optional)

## Matching Algorithm

The reconciliation uses a weighted scoring system:

| Field          | Weight | Matching Logic                          |
| -------------- | ------ | --------------------------------------- |
| Supplier GSTIN | 40%    | Exact match                             |
| Invoice Number | 30%    | Fuzzy matching (configurable threshold) |
| Invoice Date   | 20%    | Date range tolerance (±days)            |
| Taxable Amount | 10%    | Amount tolerance (±rupees)              |

**Match Categories:**

- **Score ≥ 0.8**: Perfect Match
- **Score 0.5-0.8**: Partial Match (requires review)
- **Score < 0.5**: No Match

## Configuration

### Environment Variables

```bash
# Optional: Configure logging level
LOG_LEVEL=INFO

# Optional: Configure report output directory
REPORTS_DIR=./reports
```

### Matching Parameters

- `fuzzy_threshold`: 0-100 (default: 85) - Minimum similarity score for invoice numbers
- `date_tolerance`: Days (default: 2) - Maximum date difference allowed
- `amount_tolerance`: Rupees (default: 5.0) - Maximum amount difference allowed

## Reports Generated

### 1. Detailed Reconciliation Report

Complete record-level analysis with:

- Match status and scores
- Amount differences
- Actionable remarks

### 2. Summary Report

High-level metrics including:

- Total records processed
- Match statistics
- Amount summaries

### 3. Exception Reports

- **GSTR Unmatched**: Records in GSTR not found in Books
- **Books Unmatched**: Records in Books not found in GSTR
- **Partial Matches**: Records requiring manual review

## Usage Examples

### Python Script

```python
from gst_reco.main import kickoff_gst_reconciliation

# Sample data
gstr_data = {...}  # Your GSTR JSON data
books_file_path = "books_data.xlsx"

# Run reconciliation
results = kickoff_gst_reconciliation(
    gstr_json=gstr_data,
    books_file_path=books_file_path,
    company_id="COMPANY123",
    sheet_name="Book ITC"
)

print(f"Match percentage: {results['summary']['match_percentage']}%")
```

### FastAPI Integration

The module is integrated with the main FastAPI application and available at `/gst-reconcile` endpoint.

## Error Handling

The system handles various error scenarios:

- Invalid JSON format in GSTR data
- Missing or corrupt Excel files
- Invalid sheet names
- Data format inconsistencies
- Network and file system errors

All errors are logged and returned with appropriate HTTP status codes.

## Compliance Features

- **Indian GST Specific**: Designed for Indian GST regulations
- **GSTR-2A/2B Compatibility**: Handles official GST portal JSON format
- **Audit Trail**: Comprehensive logging and reporting
- **Data Security**: Temporary file handling with automatic cleanup

## Performance

- **Efficient Processing**: Optimized for large datasets
- **Memory Management**: Streaming processing for large files
- **Parallel Processing**: Multi-threaded operations where applicable
- **Scalable**: Designed to handle enterprise-scale data volumes

## Support

For technical support or questions, refer to the main project documentation or contact the development team.
