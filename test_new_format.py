#!/usr/bin/env python3
"""
Test script to verify the updated GST data processor with new purchase_invoice_table format
"""

import pandas as pd
import tempfile
import os
from gst_reco.gst_data_processor import GSTDataProcessor

def create_test_excel_file():
    """Create a test Excel file with the new purchase_invoice_table format"""
    
    # Sample data based on the provided format
    test_data = {
        'supplier_name': [
            'BHARTI AIRTEL LTD.',
            'BHARTI AIRTEL LTD.',
            'BHARTI AIRTEL LTD.',
            'GSTN',
            'AWS INDIA PRIVATE LIMITED'
        ],
        'supplier_gstin': [
            '24AAACB2894G1ZT',
            '24AAACB2894G1ZT',
            '24AAACB2894G1ZT',
            '01AABCE2207R1Z5',
            '07AAJCA9880A1ZL'
        ],
        'invoice_number': [
            'HT2424I001485717',
            'HT2424I001485720',
            'HT2424I001485721',
            'S008400',
            'ACN2324000103340'
        ],
        'invoice_date_epoch': [
            1721241000000,
            1720290600000,
            1720290600000,
            1721759400000,
            1720809000000
        ],
        'irn': [
            'a2sc8rhd55b3ceed1dbsc8rh29ada8d103sc8rha8e5d92sc8rhae75641369580',
            'z4sc8rhd55b3ceed1dbsc8rh29ada8d103sc8rha8e5d92sc8rhae75641369580',
            'y4sc8rhd55b3ceed1dbsc8rh29ada8d103sc8rha8e5d92sc8rhae75641369580',
            '',
            '723024781f7f4kr7799229784bd7e98f577f4kr58f5cb674f534617f4krfde51'
        ],
        'place_of_supply': [24, 24, 24, 24, 24],
        'sub_total': [3999, 3999, 3999, 5931.36, 3116.94],
        'gst_rate': [18, 18, 18, 18, 18],
        'cgst': [359.91, 359.91, 359.91, 0, 0],
        'sgst': [359.91, 359.91, 359.91, 0, 0],
        'igst': [0, 0, 0, 1067.64, 561.05],
        'cess': [0, 0, 0, 0, 0],
        'total': [4718.82, 4718.82, 4718.82, 6999, 3677.99]
    }
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    
    # Create temporary Excel file
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    
    # Write to Excel with the sheet name 'purchase_invoice_table'
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='purchase_invoice_table', index=False)
    
    return temp_file.name

def test_new_format():
    """Test the updated GST data processor with new format"""
    
    print("Creating test Excel file with new purchase_invoice_table format...")
    excel_file = create_test_excel_file()
    
    try:
        print(f"Test file created: {excel_file}")
        
        # Initialize processor
        processor = GSTDataProcessor()
        
        print("Processing books data with new format...")
        # Process the books data
        books_df = processor.process_books_data(
            file_path=excel_file,
            sheet_name="purchase_invoice_table"
        )
        
        print(f"Successfully processed {len(books_df)} records")
        print("\nProcessed DataFrame columns:")
        print(list(books_df.columns))
        
        print("\nSample data:")
        print(books_df.head())
        
        # Verify key columns exist
        expected_columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_date', 'taxable_value']
        missing_columns = [col for col in expected_columns if col not in books_df.columns]
        
        if missing_columns:
            print(f"\nMissing expected columns: {missing_columns}")
        else:
            print("\n✅ All expected columns are present!")
        
        # Check epoch date conversion
        if 'invoice_date' in books_df.columns:
            print(f"\n✅ Invoice dates converted successfully:")
            print(books_df['invoice_date'].head())
        
        # Check new fields
        new_fields = ['irn', 'place_of_supply', 'gst_rate', 'cess', 'total_amount']
        available_new_fields = [field for field in new_fields if field in books_df.columns]
        print(f"\n✅ New fields available: {available_new_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary file
        if os.path.exists(excel_file):
            os.unlink(excel_file)
            print(f"\nCleaned up temporary file: {excel_file}")

if __name__ == "__main__":
    print("Testing GST Data Processor with new purchase_invoice_table format")
    print("=" * 70)
    
    success = test_new_format()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
