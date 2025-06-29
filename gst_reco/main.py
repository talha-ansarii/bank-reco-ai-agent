from .gst_data_processor import GSTReconciliationEngine
from .report_generator import GSTReportGenerator
import tempfile
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def kickoff_gst_reconciliation(
    gstr_json: Dict,
    books_file_path: str,
    company_id: str = None,
    sheet_name: str = "Book ITC",
    fuzzy_threshold: int = 85,
    date_tolerance: int = 2,
    amount_tolerance: float = 5.0
) -> Dict[str, Any]:
    """
    Main function to perform GST reconciliation

    Args:
        gstr_json: GSTR-2A/2B JSON data
        books_file_path: Path to Books Excel file
        company_id: Company identifier
        sheet_name: Excel sheet name containing books data
        fuzzy_threshold: Fuzzy matching threshold for invoice numbers
        date_tolerance: Date tolerance in days
        amount_tolerance: Amount tolerance in rupees

    Returns:
        Dict containing reconciliation results and report paths
    """
    try:
        logger.info(f"Starting GST reconciliation for company: {company_id}")

        # Initialize reconciliation engine
        engine = GSTReconciliationEngine(
            fuzzy_threshold=fuzzy_threshold,
            date_tolerance=date_tolerance,
            amount_tolerance=amount_tolerance
        )

        # Perform reconciliation
        reconciliation_results = engine.reconcile(
            gstr_json=gstr_json,
            books_file_path=books_file_path,
            sheet_name=sheet_name
        )

        if reconciliation_results.get("status") == "error":
            return reconciliation_results

        # Generate reports
        report_generator = GSTReportGenerator()
        report_paths = report_generator.generate_all_reports(
            reconciliation_results=reconciliation_results,
            company_id=company_id
        )

        # Add report paths to results
        reconciliation_results["report_paths"] = report_paths

        logger.info("GST reconciliation completed successfully")
        return reconciliation_results

    except Exception as e:
        logger.error(f"GST reconciliation failed: {str(e)}")
        return {
            "status": "error",
            "message": f"GST reconciliation failed: {str(e)}"
        }
