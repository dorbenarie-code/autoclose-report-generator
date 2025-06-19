from myapp.utils.logger_config import get_logger
from myapp.utils.logger_config import get_logger as setup_logger  # type: ignore[import-not-found]

log = get_logger(__name__)
logger = log
import os
import pandas as pd
from typing import List, Set, Union, Tuple, Optional, Any, Iterable
from pathlib import Path
import re

# Constants for validation
MAX_FILE_SIZE_MB = 10  # Maximum file size in MB
MAX_FILES_PER_UPLOAD = 5  # Maximum number of files per upload
ALLOWED_EXTENSIONS = {".xls", ".xlsx", ".csv"}

# Based on original implementation fileciteturn0file0

# List of columns that must appear in every report
typing_List = List[str]  # alias for readability
REQUIRED_COLUMNS: List[str] = [
    "name",
    "phone",
    "job_id",
    "address",
    "service_type",
    "car",
    "notes",
    "technician",
    "payment_type",
    "total",
    "parts",
    "code",
    "timestamp",
]

# Mapping of standard column names to possible alias names
COLUMN_ALIASES = {
    "name": ["clientname", "שם", "full_name"],
    "phone": ["phone_number", "טלפון", "contact"],
    "job_id": ["jobid", "id", "record_id"],
    "address": ["addr", "כתובת", "location"],
    "service_type": ["job_type", "service", "type"],
    "car": ["car_info", "vehicle", "license_plate"],
    "notes": ["remarks", "comments", "technician_notes"],
    "technician": ["tech", "worker", "employee"],
    "payment_type": ["payment", "payment_method", "pay_type"],
    "total": ["amount", "final_sum", "cost"],
    "parts": ["parts_cost", "spare_parts", "parts_price"],
    "code": ["internal_code", "job_id"],
    "timestamp": ["created"],
}


class InvalidCSVError(Exception):
    pass


def _find_missing_columns(actual: set[str], required: set[str]) -> set[str]:
    """Identify which required columns are absent from the actual columns."""
    return required - actual


def _format_missing_columns(missing: set[str]) -> str:
    """Format missing column names for logging."""
    return ", ".join(sorted(missing))


def _load_csv(path: str) -> pd.DataFrame:
    """Load a CSV file with robust parsing; skip bad lines."""
    try:
        return pd.read_csv(
            path, sep=",", quotechar='"', engine="python", on_bad_lines="skip"
        )
    except Exception as e:
        logger.error(f"[CSV LOAD] Could not read '{path}': {e}")
        raise


def _load_excel(path: str) -> pd.DataFrame:
    """Load an Excel file using openpyxl engine."""
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        logger.error(f"[EXCEL LOAD] Could not read '{path}': {e}")
        raise


def load_file(filepath: str | Path) -> pd.DataFrame:
    """
    1. Verify that the path exists and is a file.
    2. Dispatch to CSV or Excel loader.
    """
    p = Path(filepath)
    if not p.is_file():
        logger.error("File not found or is not a file: %s", p)
        raise FileNotFoundError(f"No such file: {p}")

    ext = p.suffix.lower()
    if ext == ".csv":
        return _load_csv(str(p))
    if ext in {".xls", ".xlsx"}:
        return _load_excel(str(p))
    raise ValueError(f"Unsupported file type: '{ext}'")


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip whitespace, lowercase, replace spaces with underscores on column names.
    """
    cleaned = {col: col.strip().lower().replace(" ", "_") for col in df.columns}
    return df.rename(columns=cleaned)


def _rename_alias_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename any columns matching aliases to their standard names.
    """
    for standard, aliases in COLUMN_ALIASES.items():
        if standard not in df.columns:
            for alt in aliases:
                if alt in df.columns:
                    df = df.rename(columns={alt: standard})
                    break
    return df


def _fill_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Log and fill missing required columns with None.
    """
    actual = set(df.columns)
    required = set(REQUIRED_COLUMNS)
    missing = _find_missing_columns(actual, required)
    if missing:
        logger.warning(
            f"[COLUMN WARNING] Missing columns: {_format_missing_columns(missing)}"
        )
        for col in missing:
            df[col] = None
    return df


def _drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where all values are NaN."""
    return df.dropna(how="all")


def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Full pipeline:
    1. Load CSV or Excel file
    2. Normalize column names
    3. Rename aliases
    4. Fill missing columns (logged warnings)
    5. Drop fully empty rows

    Returns a cleaned DataFrame.
    """
    df = load_file(filepath)
    df = _normalize_column_names(df)
    df = _rename_alias_columns(df)
    df = _fill_missing_columns(df)
    df = _drop_empty_rows(df)
    return df


def _check_column_validity(df: pd.DataFrame) -> tuple[bool, set[str], set[str]]:
    """
    Returns:
        is_valid: bool (True if all critical columns exist)
        missing_crit: set of missing critical columns
        missing_imp: set of missing important columns
    """
    # נגדיר קריטיות וחשובות (דוגמה: job_id, technician, date קריטיות)
    critical = {"job_id", "technician", "date"}
    important = {"service_type", "amount", "client_name"}
    actual = set(df.columns)
    missing_crit = critical - actual
    missing_imp = important - actual
    is_valid = not missing_crit
    return is_valid, missing_crit, missing_imp


def validate_and_load_file(filepath: str | Path) -> tuple[pd.DataFrame, str]:
    """
    Loads, validates, and logs missing columns.
    Returns:
        df: the cleaned dataframe
        status: one of ["ok", "partial", "fail"]
    """
    df = load_and_clean_data(str(filepath))
    df.dropna(how="all", inplace=True)

    is_valid, missing_crit, missing_imp = _check_column_validity(df)

    if not is_valid:
        logger.warning(f"[VALIDATION FAIL] Missing critical columns: {missing_crit}")
        raise ValueError(f"חסרות עמודות חיוניות: {', '.join(missing_crit)}")

    if missing_imp:
        logger.warning(f"[VALIDATION PARTIAL] Missing important columns: {missing_imp}")
        return df, "partial"

    return df, "ok"


def validate_file_extension(filename: str) -> bool:
    """
    Validate if the file extension is supported.

    Args:
        filename (str): The name of the file to validate

    Returns:
        bool: True if the file extension is supported, False otherwise
    """
    if not filename:
        return False

    ext = os.path.splitext(filename)[1].lower()
    return ext in {".xls", ".xlsx", ".csv"}


def validate_file_size(file_path: str) -> bool:
    """
    Validate if the file size is within acceptable limits.

    Args:
        file_path (str): Path to the file to validate

    Returns:
        bool: True if file size is acceptable, False otherwise
    """
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        if size_mb > MAX_FILE_SIZE_MB:
            logger.warning(
                f"File {file_path} exceeds maximum size of {MAX_FILE_SIZE_MB}MB"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking file size: {e}")
        return False


def validate_file_count(files: list[Any]) -> bool:
    """
    Validate if the number of files is within acceptable limits.

    Args:
        files (List): List of files to validate

    Returns:
        bool: True if number of files is acceptable, False otherwise
    """
    if len(files) > MAX_FILES_PER_UPLOAD:
        logger.warning(
            f"Too many files uploaded: {len(files)} (max: {MAX_FILES_PER_UPLOAD})"
        )
        return False
    return True


def validate_email(email: str) -> bool:
    """
    Comprehensive email validation.

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        logger.warning("Email is empty or not a string")
        return False

    # Remove any whitespace
    email = email.strip()

    # Check basic format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        logger.warning(f"Invalid email format: {email}")
        return False

    # Additional checks
    try:
        # Split into local part and domain
        local_part, domain = email.split("@")

        # Check local part length (max 64 chars)
        if len(local_part) > 64:
            logger.warning(f"Local part too long: {local_part}")
            return False

        # Check domain length (max 255 chars)
        if len(domain) > 255:
            logger.warning(f"Domain too long: {domain}")
            return False

        # Check for consecutive dots
        if ".." in local_part or ".." in domain:
            logger.warning("Consecutive dots found in email")
            return False

        # Check for valid TLD (at least 2 chars)
        tld = domain.split(".")[-1]
        if len(tld) < 2:
            logger.warning(f"Invalid TLD: {tld}")
            return False

    except Exception as e:
        logger.warning(f"Email validation error: {str(e)}")
        return False

    return True


def validate_file(df: pd.DataFrame, *, required: Iterable[str] = None) -> pd.DataFrame:
    if required is None:
        required = {"job_id", "total", "parts"}
    missing = set(required) - set(df.columns)
    if missing:
        raise InvalidCSVError(f"Missing required columns: {', '.join(missing)}")
    return df


def raise_if_invalid(file_path: str) -> None:
    """Raise an exception if the file is invalid (not found or unsupported type)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.suffix.lower() in [".xlsx", ".xls", ".csv"]:
        raise InvalidCSVError(f"Unsupported file type: {path.suffix}")
