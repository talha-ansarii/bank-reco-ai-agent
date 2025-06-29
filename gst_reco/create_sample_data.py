"""
Sample Books Data Generator
Creates a sample Excel file with Books of Accounts data for testing
"""

import pandas as pd
from datetime import datetime, timedelta
import random


def create_sample_books_data():
    """Create sample Books of Accounts data"""

    # Sample data
    sample_data = [
        {
            'GSTIN': '24ABKCS2033B1ZV',
            'Invoice No': '11129',
            'Invoice Date': '13-01-2025',
            'Taxable Value': 999.00,
            'IGST': 179.82,
            'CGST': 0.00,
            'SGST': 0.00,
            'Total GST': 179.82
        },
        {
            'GSTIN': '24ABKCS2033B1ZV',
            'Invoice No': '11652',
            'Invoice Date': '13-02-2025',
            'Taxable Value': 2699.00,
            'IGST': 485.82,
            'CGST': 0.00,
            'SGST': 0.00,
            'Total GST': 485.82
        },
        {
            'GSTIN': '33AAUCA1846M1Z8',
            'Invoice No': 'AL-2425-0038',
            'Invoice Date': '07-03-2025',
            'Taxable Value': 143885.00,
            'IGST': 25899.30,
            'CGST': 0.00,
            'SGST': 0.00,
            'Total GST': 25899.30
        },
        {
            'GSTIN': 'BOOKS_ONLY_GSTIN1',
            'Invoice No': 'BOOKS_ONLY_001',
            'Invoice Date': '15-03-2025',
            'Taxable Value': 5000.00,
            'IGST': 900.00,
            'CGST': 0.00,
            'SGST': 0.00,
            'Total GST': 900.00
        },
        {
            'GSTIN': '29AACCT3705E1ZJ',
            'Invoice No': 'I/O/003699/25-26',
            'Invoice Date': '03-04-2025',
            'Taxable Value': 885.00,
            'IGST': 0.00,
            'CGST': 79.65,
            'SGST': 79.65,
            'Total GST': 159.30
        }
    ]

    # Create DataFrame
    df = pd.DataFrame(sample_data)

    # Convert date column
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], format='%d-%m-%Y')

    return df


def save_sample_excel(filename='sample_books_data.xlsx'):
    """Save sample data to Excel file"""

    df = create_sample_books_data()

    # Create Excel writer
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Write to 'Book ITC' sheet
        df.to_excel(writer, sheet_name='Book ITC', index=False)

        # Add some formatting
        workbook = writer.book
        worksheet = writer.sheets['Book ITC']

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"Sample Excel file created: {filename}")
    print(f"Sheet name: 'Book ITC'")
    print(f"Records: {len(df)}")
    print("\nSample data preview:")
    print(df.to_string(index=False))

    return filename


if __name__ == "__main__":
    save_sample_excel()
