from myapp.utils.logger_config import get_logger
from myapp.utils.date_utils import parse_date_flex

log = get_logger(__name__)
# myapp/utils/parsers.py

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd


def parse_date(value: str) -> Optional[datetime]:
    """
    Tries to parse a date string in various common formats.
    Returns a datetime object or raises ValueError if parsing fails.
    """
    if not value:
        return None

    try:
        return parse_date_flex(value.strip())
    except Exception:
        raise ValueError(f"Unrecognized date format: '{value}'")


def filter_records_by_date(
    records: list[dict[str, Any]],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> list[dict[str, Any]]:
    """
    Filters a list of records by a 'date' field between start_date and end_date.
    Records without valid date are skipped.
    """
    # Guard clause: if either date is None, return empty list to avoid TypeError
    if start_date is None or end_date is None:
        return []

    result = []
    for record in records:
        record_date_str = record.get("date") or record.get("report_date")
        if not record_date_str:
            continue

        try:
            record_date = parse_date(str(record_date_str))
            if record_date is not None and start_date <= record_date <= end_date:
                result.append(record)
        except Exception:
            continue

    return result


def parse_dates_in_columns(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    """
    Parse date columns in a DataFrame to datetime objects.
    """
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def dates_in_order(date_from: Optional[datetime], date_to: Optional[datetime]) -> bool:
    """Return True if both dates are not None and date_from <= date_to, else False."""
    if date_from is None or date_to is None:
        return False
    return date_from <= date_to
