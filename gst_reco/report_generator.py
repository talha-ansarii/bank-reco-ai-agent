import pandas as pd
import csv
import json
from datetime import datetime
from typing import Dict, List, Any
import os
import logging

logger = logging.getLogger(__name__)


class GSTReportGenerator:
    """Generate various reports for GST reconciliation results"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all_reports(self, reconciliation_results: Dict[str, Any], company_id: str = None) -> Dict[str, str]:
        """
        Generate all reconciliation reports

        Args:
            reconciliation_results: Results from reconciliation engine
            company_id: Company identifier for file naming

        Returns:
            Dict containing paths to generated reports
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_prefix = f"{company_id}_" if company_id else ""

            report_paths = {}

            # 1. Detailed Reconciliation Report
            detailed_report_path = os.path.join(
                self.output_dir,
                f"{company_prefix}gst_reconciliation_detailed_{timestamp}.csv"
            )
            self._generate_detailed_report(
                reconciliation_results, detailed_report_path)
            report_paths["detailed_report"] = detailed_report_path

            # 2. Summary Report
            summary_report_path = os.path.join(
                self.output_dir,
                f"{company_prefix}gst_reconciliation_summary_{timestamp}.csv"
            )
            self._generate_summary_report(
                reconciliation_results, summary_report_path)
            report_paths["summary_report"] = summary_report_path

            # 3. Unmatched GSTR Records
            gstr_unmatched_path = os.path.join(
                self.output_dir,
                f"{company_prefix}gstr_unmatched_{timestamp}.csv"
            )
            self._generate_unmatched_gstr_report(
                reconciliation_results, gstr_unmatched_path)
            report_paths["gstr_unmatched"] = gstr_unmatched_path

            # 4. Unmatched Books Records
            books_unmatched_path = os.path.join(
                self.output_dir,
                f"{company_prefix}books_unmatched_{timestamp}.csv"
            )
            self._generate_unmatched_books_report(
                reconciliation_results, books_unmatched_path)
            report_paths["books_unmatched"] = books_unmatched_path

            # 5. Partial Matches Report
            partial_matches_path = os.path.join(
                self.output_dir,
                f"{company_prefix}partial_matches_{timestamp}.csv"
            )
            self._generate_partial_matches_report(
                reconciliation_results, partial_matches_path)
            report_paths["partial_matches"] = partial_matches_path

            logger.info(f"Generated {len(report_paths)} reports")
            return report_paths

        except Exception as e:
            logger.error(f"Error generating reports: {str(e)}")
            raise

    def _generate_detailed_report(self, results: Dict[str, Any], file_path: str):
        """Generate detailed reconciliation report"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow([
                'Supplier GSTIN',
                'Invoice No (GSTR)',
                'Invoice No (Books)',
                'Invoice Date (GSTR)',
                'Invoice Date (Books)',
                'Taxable Value (GSTR)',
                'Taxable Value (Books)',
                'GST Amount (Books)',
                'Amount Difference',
                'Match Status',
                'Match Score',
                'Remarks'
            ])

            # Matched records
            for record in results.get('matched_records', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no_gstr', ''),
                    record.get('invoice_no_books', ''),
                    self._format_date(record.get('invoice_date_gstr')),
                    self._format_date(record.get('invoice_date_books')),
                    record.get('taxable_value_gstr', 0),
                    record.get('taxable_value_books', 0),
                    record.get('gst_amount_books', 0),
                    record.get('amount_difference', 0),
                    record.get('match_status', ''),
                    record.get('match_score', 0),
                    'Perfect Match'
                ])

            # Partial matches
            for record in results.get('partial_matches', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no_gstr', ''),
                    record.get('invoice_no_books', ''),
                    self._format_date(record.get('invoice_date_gstr')),
                    self._format_date(record.get('invoice_date_books')),
                    record.get('taxable_value_gstr', 0),
                    record.get('taxable_value_books', 0),
                    record.get('gst_amount_books', 0),
                    record.get('amount_difference', 0),
                    record.get('match_status', ''),
                    record.get('match_score', 0),
                    'Requires Review'
                ])

            # GSTR only records
            for record in results.get('gstr_only_records', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no', ''),
                    '',
                    self._format_date(record.get('invoice_date')),
                    '',
                    record.get('taxable_value', 0),
                    '',
                    '',
                    '',
                    record.get('match_status', ''),
                    '',
                    'Present in GSTR only - Missing in Books'
                ])

            # Books only records
            for record in results.get('books_only_records', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    '',
                    record.get('invoice_no', ''),
                    '',
                    self._format_date(record.get('invoice_date')),
                    '',
                    record.get('taxable_value', 0),
                    record.get('gst_amount', 0),
                    '',
                    record.get('match_status', ''),
                    '',
                    'Present in Books only - Missing in GSTR'
                ])

    def _generate_summary_report(self, results: Dict[str, Any], file_path: str):
        """Generate summary report"""
        summary = results.get('summary', {})

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(['GST Reconciliation Summary'])
            writer.writerow(['Metric', 'Count', 'Amount (₹)'])
            writer.writerow(
                ['Total Records', summary.get('total_records', 0), ''])
            writer.writerow(['Matched Records', summary.get(
                'matched_count', 0), summary.get('matched_amount_gstr', 0)])
            writer.writerow(
                ['Partial Matches', summary.get('partial_match_count', 0), ''])
            writer.writerow(['GSTR Only Records', summary.get(
                'gstr_only_count', 0), summary.get('gstr_only_amount', 0)])
            writer.writerow(['Books Only Records', summary.get(
                'books_only_count', 0), summary.get('books_only_amount', 0)])
            writer.writerow(
                ['Match Percentage', f"{summary.get('match_percentage', 0)}%", ''])
            writer.writerow(
                ['Amount Difference', '', summary.get('amount_difference', 0)])

    def _generate_unmatched_gstr_report(self, results: Dict[str, Any], file_path: str):
        """Generate unmatched GSTR records report"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow([
                'Supplier GSTIN',
                'Invoice No',
                'Invoice Date',
                'Taxable Value',
                'Action Required'
            ])

            for record in results.get('gstr_only_records', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no', ''),
                    self._format_date(record.get('invoice_date')),
                    record.get('taxable_value', 0),
                    'Check if invoice is recorded in books'
                ])

    def _generate_unmatched_books_report(self, results: Dict[str, Any], file_path: str):
        """Generate unmatched books records report"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow([
                'Supplier GSTIN',
                'Invoice No',
                'Invoice Date',
                'Taxable Value',
                'GST Amount',
                'Action Required'
            ])

            for record in results.get('books_only_records', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no', ''),
                    self._format_date(record.get('invoice_date')),
                    record.get('taxable_value', 0),
                    record.get('gst_amount', 0),
                    'Verify if invoice appears in GSTR-2A/2B'
                ])

    def _generate_partial_matches_report(self, results: Dict[str, Any], file_path: str):
        """Generate partial matches report"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow([
                'Supplier GSTIN',
                'Invoice No (GSTR)',
                'Invoice No (Books)',
                'Invoice Date (GSTR)',
                'Invoice Date (Books)',
                'Taxable Value (GSTR)',
                'Taxable Value (Books)',
                'Match Score',
                'Action Required'
            ])

            for record in results.get('partial_matches', []):
                writer.writerow([
                    record.get('supplier_gstin', ''),
                    record.get('invoice_no_gstr', ''),
                    record.get('invoice_no_books', ''),
                    self._format_date(record.get('invoice_date_gstr')),
                    self._format_date(record.get('invoice_date_books')),
                    record.get('taxable_value_gstr', 0),
                    record.get('taxable_value_books', 0),
                    record.get('match_score', 0),
                    'Manual verification required'
                ])

    def _format_date(self, date_value) -> str:
        """Format date for CSV output"""
        if pd.isna(date_value) or date_value is None:
            return ''

        if isinstance(date_value, str):
            return date_value

        try:
            return date_value.strftime('%d-%m-%Y')
        except:
            return str(date_value)

    def generate_json_report(self, results: Dict[str, Any], file_path: str):
        """Generate JSON format report"""
        try:
            # Convert pandas timestamps to strings for JSON serialization
            json_results = self._convert_for_json(results)

            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_results, jsonfile, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            raise

    def _convert_for_json(self, data):
        """Convert data to JSON-serializable format"""
        if isinstance(data, dict):
            return {key: self._convert_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_for_json(item) for item in data]
        elif pd.isna(data):
            return None
        elif hasattr(data, 'isoformat'):  # datetime objects
            return data.isoformat()
        else:
            return data
