import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Union, Any
import logging

logger = logging.getLogger(__name__)


def clean_gstin(gstin: str) -> str:
    """
    Clean and validate GSTIN format

    Args:
        gstin: Raw GSTIN string

    Returns:
        Cleaned GSTIN string
    """
    if pd.isna(gstin) or gstin == "":
        return ""

    gstin = str(gstin).upper().strip()
    # Remove any spaces or special characters except alphanumeric
    gstin = re.sub(r'[^A-Z0-9]', '', gstin)

    # Basic GSTIN validation (15 characters)
    if len(gstin) == 15:
        return gstin
    else:
        logger.warning(f"Invalid GSTIN format: {gstin}")
        return gstin


def clean_invoice_number(invoice_no: Union[str, Any]) -> str:
    """
    Clean and normalize invoice number

    Args:
        invoice_no: Raw invoice number

    Returns:
        Cleaned invoice number
    """
    if pd.isna(invoice_no) or invoice_no == "":
        return ""

    invoice_no = str(invoice_no).strip()
    # Remove extra spaces and normalize
    invoice_no = re.sub(r'\s+', ' ', invoice_no)
    return invoice_no.upper()


def parse_amount(amount: Union[str, float, int]) -> float:
    """
    Parse amount from various formats

    Args:
        amount: Amount in various formats

    Returns:
        Float amount
    """
    if pd.isna(amount) or amount == "":
        return 0.0

    if isinstance(amount, (int, float)):
        return float(amount)

    # Remove currency symbols and commas
    amount_str = str(amount).replace(',', '').replace(
        '₹', '').replace('Rs', '').strip()

    try:
        return float(amount_str)
    except ValueError:
        logger.warning(f"Could not parse amount: {amount}")
        return 0.0


def standardize_date(date_value: Union[str, datetime, pd.Timestamp]) -> pd.Timestamp:
    """
    Standardize date format

    Args:
        date_value: Date in various formats

    Returns:
        Standardized pandas Timestamp
    """
    if pd.isna(date_value) or date_value == "":
        return pd.NaT

    if isinstance(date_value, (pd.Timestamp, datetime)):
        return pd.Timestamp(date_value)

    # Try to parse string dates
    try:
        return pd.to_datetime(date_value, dayfirst=True, errors='coerce')
    except:
        logger.warning(f"Could not parse date: {date_value}")
        return pd.NaT


def calculate_gst_total(igst: float = 0, cgst: float = 0, sgst: float = 0) -> float:
    """
    Calculate total GST amount

    Args:
        igst: IGST amount
        cgst: CGST amount
        sgst: SGST amount

    Returns:
        Total GST amount
    """
    return sum([parse_amount(igst), parse_amount(cgst), parse_amount(sgst)])


def validate_gstr_json(gstr_json: dict) -> bool:
    """
    Validate GSTR JSON structure

    Args:
        gstr_json: GSTR JSON data

    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(gstr_json, dict):
            return False

        if 'data' not in gstr_json:
            return False

        if 'list' not in gstr_json['data']:
            return False

        if not isinstance(gstr_json['data']['list'], list):
            return False

        return True
    except:
        return False


def create_match_key(gstin: str, invoice_no: str, date: pd.Timestamp) -> str:
    """
    Create a unique match key for reconciliation

    Args:
        gstin: Supplier GSTIN
        invoice_no: Invoice number
        date: Invoice date

    Returns:
        Unique match key
    """
    date_str = date.strftime('%Y%m%d') if pd.notna(date) else 'NODATE'
    return f"{clean_gstin(gstin)}_{clean_invoice_number(invoice_no)}_{date_str}"


def log_data_quality_issues(df: pd.DataFrame, source: str):
    """
    Log data quality issues in the DataFrame

    Args:
        df: DataFrame to check
        source: Data source name
    """
    issues = []

    # Check for missing values
    missing_cols = df.isnull().sum()
    for col, count in missing_cols.items():
        if count > 0:
            issues.append(f"{col}: {count} missing values")

    # Check for duplicate invoice numbers
    if 'invoice_no' in df.columns:
        duplicates = df['invoice_no'].duplicated().sum()
        if duplicates > 0:
            issues.append(f"invoice_no: {duplicates} duplicate values")

    # Check for invalid dates
    if 'invoice_date' in df.columns:
        invalid_dates = df['invoice_date'].isna().sum()
        if invalid_dates > 0:
            issues.append(f"invoice_date: {invalid_dates} invalid dates")

    # Check for negative amounts
    amount_cols = ['taxable_value', 'igst', 'cgst', 'sgst', 'total_gst']
    for col in amount_cols:
        if col in df.columns:
            negative_amounts = (df[col] < 0).sum()
            if negative_amounts > 0:
                issues.append(f"{col}: {negative_amounts} negative values")

    if issues:
        logger.warning(f"Data quality issues in {source}: {'; '.join(issues)}")
    else:
        logger.info(f"No data quality issues found in {source}")


def format_currency(amount: float) -> str:
    """
    Format amount as currency

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string
    """
    return f"₹{amount:,.2f}"


def calculate_match_percentage(matched: int, total: int) -> float:
    """
    Calculate match percentage

    Args:
        matched: Number of matched records
        total: Total number of records

    Returns:
        Match percentage
    """
    if total == 0:
        return 0.0
    return round((matched / total) * 100, 2)
