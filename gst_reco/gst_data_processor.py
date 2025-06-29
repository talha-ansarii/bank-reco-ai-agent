import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json
import re
import difflib
import logging

logger = logging.getLogger(__name__)


class GSTDataProcessor:
    """Process and normalize GST data from GSTR-2A/2B and Books of Accounts"""

    def __init__(self):
        self.gstr_data = None
        self.books_data = None

    def process_gstr_data(self, gstr_json: Dict) -> pd.DataFrame:
        """
        Process GSTR-2A/2B JSON data into a normalized DataFrame
        Handles both GSTR-2A and GSTR-2B formats

        Args:
            gstr_json: JSON data from GSTR-2A/2B API

        Returns:
            pd.DataFrame: Normalized GSTR data
        """
        try:
            records = []

            # Check if it's GSTR-2B format (has 'docdata' field)
            if 'docdata' in gstr_json:
                # GSTR-2B format
                for doc in gstr_json.get('docdata', []):
                    record = {
                        'supplier_gstin': doc.get('ctin', '').upper().strip(),
                        'invoice_no': self._clean_invoice_no(doc.get('inum', '')),
                        'invoice_date': self._parse_date(doc.get('dt', '')),
                        'taxable_value': float(doc.get('txval', 0)),
                        'igst': float(doc.get('igst', 0)),
                        'cgst': float(doc.get('cgst', 0)),
                        'sgst': float(doc.get('sgst', 0)),
                        'total_gst': float(doc.get('igst', 0)) + float(doc.get('cgst', 0)) + float(doc.get('sgst', 0)),
                        'invoice_type': doc.get('typ', ''),
                        'place_of_supply': doc.get('pos', ''),
                        'reverse_charge': doc.get('rev', 'N'),
                        'supplier_name': doc.get('trdnm', ''),
                        'source': 'GSTR-2B'
                    }
                    records.append(record)

            # Check if it's GSTR-2A format (has 'data' and 'list' fields)
            elif 'data' in gstr_json and 'list' in gstr_json['data']:
                # GSTR-2A format
                for supplier in gstr_json['data']['list']:
                    ctin = supplier.get('ctin', '')

                    for item in supplier.get('items', []):
                        record = {
                            'supplier_gstin': ctin.upper().strip(),
                            'invoice_no': self._clean_invoice_no(item.get('inum', '')),
                            'invoice_date': self._parse_date(item.get('idt', '')),
                            'taxable_value': float(item.get('val', 0)),
                            'igst': 0,  # Not available in GSTR-2A format
                            'cgst': 0,  # Not available in GSTR-2A format
                            'sgst': 0,  # Not available in GSTR-2A format
                            'total_gst': 0,  # Not available in GSTR-2A format
                            'invoice_type': item.get('inv_typ', ''),
                            'place_of_supply': item.get('pos', ''),
                            'reverse_charge': item.get('rchrg', 'N'),
                            'supplier_name': '',  # Not available in GSTR-2A format
                            'source': 'GSTR-2A'
                        }
                        records.append(record)

            # Check if it's direct list format (simplified GSTR-2A)
            elif 'list' in gstr_json:
                # Direct list format
                for supplier in gstr_json['list']:
                    ctin = supplier.get('ctin', '')

                    for item in supplier.get('items', []):
                        record = {
                            'supplier_gstin': ctin.upper().strip(),
                            'invoice_no': self._clean_invoice_no(item.get('inum', '')),
                            'invoice_date': self._parse_date(item.get('idt', '')),
                            'taxable_value': float(item.get('val', 0)),
                            'igst': 0,
                            'cgst': 0,
                            'sgst': 0,
                            'total_gst': 0,
                            'invoice_type': item.get('inv_typ', ''),
                            'place_of_supply': item.get('pos', ''),
                            'reverse_charge': item.get('rchrg', 'N'),
                            'supplier_name': '',
                            'source': 'GSTR-2A'
                        }
                        records.append(record)
            else:
                raise ValueError(
                    "Invalid GSTR JSON format - could not identify GSTR-2A or GSTR-2B structure")

            df = pd.DataFrame(records)
            self.gstr_data = df
            logger.info(f"Processed {len(df)} GSTR records")
            return df

        except Exception as e:
            logger.error(f"Error processing GSTR data: {str(e)}")
            raise

    def process_books_data(self, file_path: str, sheet_name: str = "Book ITC") -> pd.DataFrame:
        """
        Process Books of Accounts Excel data into a normalized DataFrame

        Args:
            file_path: Path to Excel file
            sheet_name: Name of the sheet containing data

        Returns:
            pd.DataFrame: Normalized Books data
        """
        try:
            # Read Excel file and detect header row
            print(
                f"Processing Books data from {file_path}, sheet: {sheet_name}")

            # Try to auto-detect header row (could be in row 0, 1, or 2)
            header_row = self._detect_header_row(file_path, sheet_name)
            logger.info(f"Detected header row at index: {header_row}")

            # Read Excel file with detected header row
            df = pd.read_excel(
                file_path, sheet_name=sheet_name, header=header_row)

            if df.empty:
                logger.warning("Books data is empty")
                return pd.DataFrame()

            # Print original columns for debugging
            logger.warning(f"Original Excel columns: {list(df.columns)}")

            # Create column mapping based on the actual Excel structure
            # Map the exact column names from the Excel screenshot
            column_mapping = {
                # GSTIN column - handle various formats
                'GSTIN': 'supplier_gstin',
                'gstin': 'supplier_gstin',
                'Supplier GSTIN': 'supplier_gstin',
                'supplier_gstin': 'supplier_gstin',
                'Vendor GSTIN': 'supplier_gstin',
                'Party GSTIN': 'supplier_gstin',

                # Name column - handle various formats
                'Name': 'supplier_name',
                'name': 'supplier_name',
                'Vendor Name': 'supplier_name',
                'vendor_name': 'supplier_name',
                'Party Name': 'supplier_name',
                'Supplier Name': 'supplier_name',

                # Invoice Type
                'Invoice Type': 'invoice_type',
                'invoice_type': 'invoice_type',
                'Transaction Type': 'invoice_type',
                'Voucher Type': 'invoice_type',

                # Invoice Number - mapping voucher ref no to invoice no
                'Voucher Ref. No.': 'invoice_no',
                'Voucher Ref No': 'invoice_no',
                'Voucher Ref. No': 'invoice_no',
                'voucher_ref._no.': 'invoice_no',
                'voucher_ref_no': 'invoice_no',
                'Invoice No': 'invoice_no',
                'Invoice No.': 'invoice_no',
                'invoice_no': 'invoice_no',
                'Invoice Number': 'invoice_no',
                'invoice_number': 'invoice_no',
                'Bill No': 'invoice_no',
                'Bill Number': 'invoice_no',
                'Reference No': 'invoice_no',
                'Ref No': 'invoice_no',

                # Voucher No
                'Voucher No': 'voucher_no',
                'Voucher No.': 'voucher_no',
                'voucher_no': 'voucher_no',
                'Voucher Number': 'voucher_no',

                # Invoice Date - mapping voucher ref date to invoice date
                'Voucher Ref. Date': 'invoice_date',
                'Voucher Ref Date': 'invoice_date',
                'voucher_ref._date': 'invoice_date',
                'voucher_ref_date': 'invoice_date',
                'Invoice Date': 'invoice_date',
                'invoice_date': 'invoice_date',
                'Bill Date': 'invoice_date',
                'Transaction Date': 'invoice_date',
                'Date': 'invoice_date',

                # Taxable Value - handle various formats
                'Taxable Value': 'taxable_value',
                'taxable_value': 'taxable_value',
                'Taxable Amount': 'taxable_value',
                'Net Amount': 'taxable_value',
                'Base Amount': 'taxable_value',
                'Amount': 'taxable_value',

                # GST Components - handle various formats
                'IGST': 'igst',
                'igst': 'igst',
                'IGST Amount': 'igst',
                'Integrated GST': 'igst',

                'CGST': 'cgst',
                'cgst': 'cgst',
                'CGST Amount': 'cgst',
                'Central GST': 'cgst',

                'SGST': 'sgst',
                'sgst': 'sgst',
                'SGST Amount': 'sgst',
                'State GST': 'sgst',
                'UTGST': 'sgst',  # Union Territory GST maps to SGST

                # Total GST
                'Total GST': 'total_gst',
                'total_gst': 'total_gst',
                'GST Amount': 'total_gst',
                'Tax Amount': 'total_gst',

                # Source/Description
                'Source': 'source_description',
                'source': 'source_description',
                'Description': 'source_description',
                'Remarks': 'source_description',
                'Notes': 'source_description'
            }

            # Clean column names and apply mapping
            df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
            logger.warning(f"Cleaned column names: {list(df.columns)}")
            # Apply column mapping
            df_renamed = df.rename(columns=column_mapping)

            logger.info(f"Mapped columns: {list(df_renamed.columns)}")

            # Ensure required columns exist
            required_columns = ['supplier_gstin',
                                'invoice_no', 'invoice_date', 'taxable_value']
            missing_columns = [
                col for col in required_columns if col not in df_renamed.columns]

            if missing_columns:
                logger.warning(
                    f"Missing required columns after mapping: {missing_columns}")
                # Try to find alternative column names
                available_cols = list(df_renamed.columns)
                logger.info(f"Available columns: {available_cols}")

            # Clean and normalize data
            if 'supplier_gstin' in df_renamed.columns:
                df_renamed['supplier_gstin'] = df_renamed['supplier_gstin'].astype(
                    str).str.upper().str.strip()
                # Remove any non-alphanumeric characters except spaces and dashes
                df_renamed['supplier_gstin'] = df_renamed['supplier_gstin'].apply(
                    lambda x: re.sub(r'[^A-Z0-9]', '', str(x)
                                     ) if pd.notna(x) else ''
                )

            if 'invoice_no' in df_renamed.columns:
                df_renamed['invoice_no'] = df_renamed['invoice_no'].apply(
                    self._clean_invoice_no)

            if 'invoice_date' in df_renamed.columns:
                df_renamed['invoice_date'] = pd.to_datetime(
                    df_renamed['invoice_date'], errors='coerce')

            # Handle GST amounts - convert to numeric
            gst_columns = ['igst', 'cgst', 'sgst']
            for col in gst_columns:
                if col in df_renamed.columns:
                    # Replace dashes with 0 and convert to numeric
                    df_renamed[col] = df_renamed[col].replace('-', 0)
                    df_renamed[col] = pd.to_numeric(
                        df_renamed[col], errors='coerce').fillna(0)

            # Handle taxable value
            if 'taxable_value' in df_renamed.columns:
                df_renamed['taxable_value'] = pd.to_numeric(
                    df_renamed['taxable_value'], errors='coerce').fillna(0)

            # Calculate total GST if not present
            if 'total_gst' not in df_renamed.columns:
                available_gst_cols = [
                    col for col in gst_columns if col in df_renamed.columns]
                if available_gst_cols:
                    df_renamed['total_gst'] = df_renamed[available_gst_cols].sum(
                        axis=1)
                else:
                    df_renamed['total_gst'] = 0

            # Add source identifier
            df_renamed['source'] = 'BOOKS'

            # Filter out rows with empty GSTIN or Invoice No
            initial_count = len(df_renamed)
            df_renamed = df_renamed[
                (df_renamed['supplier_gstin'].notna()) &
                (df_renamed['supplier_gstin'] != '') &
                (df_renamed['invoice_no'].notna()) &
                (df_renamed['invoice_no'] != '')
            ]
            final_count = len(df_renamed)

            if initial_count != final_count:
                logger.info(
                    f"Filtered out {initial_count - final_count} rows with empty GSTIN or Invoice No")

            self.books_data = df_renamed
            logger.info(f"Processed {len(df_renamed)} Books records")
            return df_renamed

        except Exception as e:
            logger.error(f"Error processing Books data: {str(e)}")
            raise

    def _clean_invoice_no(self, invoice_no: str) -> str:
        """Clean and normalize invoice number"""
        if pd.isna(invoice_no):
            return ""
        invoice_no = str(invoice_no).strip()
        # Remove special characters but keep alphanumeric and common separators
        invoice_no = re.sub(r'[^\w\-/]', '', invoice_no)
        return invoice_no.upper()

    def _parse_date(self, date_str: str) -> pd.Timestamp:
        """Parse date string to datetime"""
        if pd.isna(date_str) or date_str == "":
            return pd.NaT

        try:
            # Try different date formats
            date_formats = ['%d-%m-%Y', '%d/%m/%Y',
                            '%Y-%m-%d', '%d-%b-%y', '%d-%b-%Y']

            for fmt in date_formats:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except:
                    continue

            # If no format works, use pandas default parsing
            return pd.to_datetime(date_str, errors='coerce')

        except Exception as e:
            logger.warning(f"Could not parse date: {date_str}")
            return pd.NaT

    def _detect_header_row(self, file_path: str, sheet_name: str) -> int:
        """
        Detect the row containing column headers
        Checks rows 0, 1, and 2 to find the one with the most relevant column names

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name

        Returns:
            int: Row index containing headers (0-based)
        """
        try:
            # Expected column keywords that should appear in headers
            expected_keywords = [
                'gstin', 'name', 'invoice', 'voucher', 'date', 'taxable', 'value',
                'igst', 'cgst', 'sgst', 'ref', 'no', 'type', 'source'
            ]

            best_header_row = 0
            best_score = 0

            # Check first 3 rows for headers
            for row_idx in range(3):
                try:
                    # Read with this row as header
                    test_df = pd.read_excel(
                        file_path, sheet_name=sheet_name, header=row_idx, nrows=1)

                    if test_df.empty:
                        continue

                    # Convert column names to lowercase for comparison
                    column_names = [str(col).lower().strip()
                                    for col in test_df.columns]

                    # Skip if columns are mostly unnamed or numeric
                    unnamed_count = sum(1 for col in column_names if 'unnamed' in col.lower(
                    ) or col.startswith('untitled'))
                    # More than 50% unnamed columns
                    if unnamed_count > len(column_names) * 0.5:
                        continue

                    # Calculate score based on matching keywords
                    score = 0
                    for col_name in column_names:
                        for keyword in expected_keywords:
                            if keyword in col_name:
                                score += 1
                                break

                    # Bonus points if we find key columns
                    key_columns = ['gstin', 'invoice', 'voucher', 'taxable']
                    for col_name in column_names:
                        for key_col in key_columns:
                            if key_col in col_name:
                                score += 2
                                break

                    logger.info(
                        f"Row {row_idx} score: {score}, columns: {column_names[:5]}...")

                    if score > best_score:
                        best_score = score
                        best_header_row = row_idx

                except Exception as e:
                    logger.warning(
                        f"Error checking row {row_idx} as header: {str(e)}")
                    continue

            logger.info(
                f"Selected header row {best_header_row} with score {best_score}")
            return best_header_row

        except Exception as e:
            logger.warning(
                f"Error detecting header row: {str(e)}, defaulting to row 0")
            return 0


class GSTReconciliationEngine:
    """Main reconciliation engine for GST data"""

    def __init__(self, fuzzy_threshold: int = 85, date_tolerance: int = 2, amount_tolerance: float = 5.0):
        self.fuzzy_threshold = fuzzy_threshold
        self.date_tolerance = date_tolerance
        self.amount_tolerance = amount_tolerance
        self.processor = GSTDataProcessor()

    def reconcile(self, gstr_json: Dict, books_file_path: str, sheet_name: str = "Book ITC") -> Dict[str, Any]:
        """
        Perform complete GST reconciliation

        Args:
            gstr_json: GSTR-2A/2B JSON data
            books_file_path: Path to Books Excel file
            sheet_name: Sheet name in Excel file

        Returns:
            Dict containing reconciliation results
        """
        try:
            # Process data
            gstr_df = self.processor.process_gstr_data(gstr_json)
            books_df = self.processor.process_books_data(
                books_file_path, sheet_name)

            print(
                f"Reconciliation started with {str(gstr_df.head())} GSTR records and {str(books_df.head())} Books records")
            # Perform matching
            results = self._perform_matching(gstr_df, books_df)

            # Generate summary
            summary = self._generate_summary(results)

            return {
                "status": "success",
                "summary": summary,
                "matched_records": results['matched'],
                "gstr_only_records": results['gstr_only'],
                "books_only_records": results['books_only'],
                "partial_matches": results['partial_matches']
            }

        except Exception as e:
            logger.error(f"Reconciliation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _perform_matching(self, gstr_df: pd.DataFrame, books_df: pd.DataFrame) -> Dict[str, List]:
        """Perform the actual matching logic"""
        matched = []
        partial_matches = []
        gstr_matched_indices = set()
        books_matched_indices = set()

        # Iterate through GSTR records
        for gstr_idx, gstr_row in gstr_df.iterrows():
            best_match = None
            best_score = 0
            best_books_idx = None

            # Try to find matches in books
            for books_idx, books_row in books_df.iterrows():
                if books_idx in books_matched_indices:
                    continue

                match_score = self._calculate_match_score(gstr_row, books_row)

                if match_score > best_score:
                    best_score = match_score
                    best_match = books_row
                    best_books_idx = books_idx

            # Classify the match
            if best_score >= 0.8:  # Strong match
                match_record = self._create_match_record(
                    gstr_row, best_match, "MATCHED", best_score)
                matched.append(match_record)
                gstr_matched_indices.add(gstr_idx)
                books_matched_indices.add(best_books_idx)
            elif best_score >= 0.5:  # Partial match
                match_record = self._create_match_record(
                    gstr_row, best_match, "PARTIAL_MATCH", best_score)
                partial_matches.append(match_record)
                gstr_matched_indices.add(gstr_idx)
                books_matched_indices.add(best_books_idx)

        # Unmatched GSTR records
        gstr_only = []
        for gstr_idx, gstr_row in gstr_df.iterrows():
            if gstr_idx not in gstr_matched_indices:
                gstr_only.append(
                    self._create_unmatched_record(gstr_row, "GSTR_ONLY"))

        # Unmatched Books records
        books_only = []
        for books_idx, books_row in books_df.iterrows():
            if books_idx not in books_matched_indices:
                books_only.append(self._create_unmatched_record(
                    books_row, "BOOKS_ONLY"))

        return {
            "matched": matched,
            "partial_matches": partial_matches,
            "gstr_only": gstr_only,
            "books_only": books_only
        }

    def _calculate_match_score(self, gstr_row: pd.Series, books_row: pd.Series) -> float:
        """Calculate match score between GSTR and Books records"""
        score = 0.0

        # GSTIN match (40% weight)
        if pd.notna(gstr_row.get('supplier_gstin')) and pd.notna(books_row.get('supplier_gstin')):
            if gstr_row['supplier_gstin'] == books_row['supplier_gstin']:
                score += 0.4

        # Invoice number match (30% weight)
        if pd.notna(gstr_row.get('invoice_no')) and pd.notna(books_row.get('invoice_no')):
            # Use difflib for fuzzy matching
            fuzzy_score = difflib.SequenceMatcher(
                None, str(gstr_row['invoice_no']), str(books_row['invoice_no'])).ratio() * 100
            if fuzzy_score >= self.fuzzy_threshold:
                score += 0.3 * (fuzzy_score / 100)

        # Date match (20% weight)
        if pd.notna(gstr_row.get('invoice_date')) and pd.notna(books_row.get('invoice_date')):
            date_diff = abs(
                (gstr_row['invoice_date'] - books_row['invoice_date']).days)
            if date_diff <= self.date_tolerance:
                score += 0.2 * (1 - date_diff / self.date_tolerance)

        # Amount match (10% weight)
        gstr_amount = float(gstr_row.get('taxable_value', 0))
        books_amount = float(books_row.get('taxable_value', 0))

        if gstr_amount > 0 and books_amount > 0:
            amount_diff = abs(gstr_amount - books_amount)
            if amount_diff <= self.amount_tolerance:
                score += 0.1 * (1 - amount_diff / self.amount_tolerance)

        return score

    def _create_match_record(self, gstr_row: pd.Series, books_row: pd.Series, status: str, score: float) -> Dict:
        """Create a match record"""
        return {
            "supplier_gstin": gstr_row.get('supplier_gstin', ''),
            "invoice_no_gstr": gstr_row.get('invoice_no', ''),
            "invoice_no_books": books_row.get('invoice_no', ''),
            "invoice_date_gstr": self._format_date_for_json(gstr_row.get('invoice_date')),
            "invoice_date_books": self._format_date_for_json(books_row.get('invoice_date')),
            "taxable_value_gstr": float(gstr_row.get('taxable_value', 0)),
            "taxable_value_books": float(books_row.get('taxable_value', 0)),
            "gst_amount_books": float(books_row.get('total_gst', 0)),
            "match_status": status,
            "match_score": round(score, 2),
            "amount_difference": float(gstr_row.get('taxable_value', 0)) - float(books_row.get('taxable_value', 0))
        }

    def _create_unmatched_record(self, row: pd.Series, status: str) -> Dict:
        """Create an unmatched record"""
        return {
            "supplier_gstin": row.get('supplier_gstin', ''),
            "invoice_no": row.get('invoice_no', ''),
            "invoice_date": self._format_date_for_json(row.get('invoice_date')),
            "taxable_value": float(row.get('taxable_value', 0)),
            "gst_amount": float(row.get('total_gst', 0)) if 'total_gst' in row else 0,
            "match_status": status,
            "source": row.get('source', '')
        }

    def _format_date_for_json(self, date_value) -> str:
        """Format date for JSON serialization"""
        if pd.isna(date_value) or date_value is None:
            return ""

        if isinstance(date_value, pd.Timestamp):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        else:
            # Try to convert to datetime if it's a string
            try:
                dt = pd.to_datetime(date_value)
                if pd.isna(dt):
                    return ""
                return dt.strftime('%Y-%m-%d')
            except:
                return str(date_value)

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate reconciliation summary"""
        total_matched = len(results['matched'])
        total_partial = len(results['partial_matches'])
        total_gstr_only = len(results['gstr_only'])
        total_books_only = len(results['books_only'])
        total_records = total_matched + total_partial + total_gstr_only + total_books_only

        # Calculate amounts
        matched_amount_gstr = sum(r['taxable_value_gstr']
                                  for r in results['matched'])
        matched_amount_books = sum(r['taxable_value_books']
                                   for r in results['matched'])

        gstr_only_amount = sum(r['taxable_value']
                               for r in results['gstr_only'])
        books_only_amount = sum(r['taxable_value']
                                for r in results['books_only'])

        return {
            "total_records": total_records,
            "matched_count": total_matched,
            "partial_match_count": total_partial,
            "gstr_only_count": total_gstr_only,
            "books_only_count": total_books_only,
            "match_percentage": round((total_matched / total_records * 100) if total_records > 0 else 0, 2),
            "matched_amount_gstr": round(matched_amount_gstr, 2),
            "matched_amount_books": round(matched_amount_books, 2),
            "gstr_only_amount": round(gstr_only_amount, 2),
            "books_only_amount": round(books_only_amount, 2),
            "amount_difference": round(matched_amount_gstr - matched_amount_books, 2)
        }
