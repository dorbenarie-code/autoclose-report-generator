from datetime import datetime
import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)

def parse_date_flex(date_input) -> datetime:
    if isinstance(date_input, datetime):
        return date_input

    if not isinstance(date_input, str):
        raise ValueError(f"❌ קלט לא נתמך (לא מחרוזת): {date_input} (type: {type(date_input)})")

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%MZ",
        "%Y/%m/%d",
        "%m/%d/%Y %I:%M %p",  # ✅ זה מה שתוקע אותך
    )

    for fmt in formats:
        try:
            return datetime.strptime(date_input.strip(), fmt)
        except Exception:
            continue

    raise ValueError(f"❌ תאריך לא נתמך (parse_date_flex): {date_input}")

def clean_and_parse_dates(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Attempts to parse date columns safely, coercing invalid formats to NaT.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame
        columns (List[str]): List of column names to parse as dates

    Returns:
        pd.DataFrame: The same DataFrame with parsed datetime columns
    """
    for col in columns:
        if col in df.columns:
            original_invalid = df[col].isnull().sum()
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)
            new_invalid = df[col].isnull().sum()

            if new_invalid > original_invalid:
                logger.warning(f"🟡 {col}: Found {new_invalid - original_invalid} invalid date values coerced to NaT")

        else:
            logger.warning(f"⚠️ Column '{col}' not found in DataFrame – skipped.")

    return df

def clean_and_parse_dates(df, cols):
    # אם כבר יש parse_date_flex
    return parse_date_flex(df, cols)
