# myapp/utils/decimal_utils.py
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
from typing import Iterable, Sequence

import pandas as pd
import logging

from myapp.utils.logger_config import get_logger

logger = get_logger("decimal_utils")

# ––––– GLOBAL DECIMAL CONTEXT –––––
getcontext().prec = 28          # עד 28 ספרות–מספיק גם למיליארדים
getcontext().rounding = ROUND_HALF_UP


_CLEAN_RE = re.compile(r"[^\d.\-]")   # cache אחת לכל המודול


def _clean_numeric_string(raw: str) -> str:
    """
    >>> _clean_numeric_string("₪1,234.56")
    '1234.56'
    """
    return _CLEAN_RE.sub("", raw.replace(",", "")).strip() or "0"


def safe_decimal(val: object) -> Decimal | None:
    try:
        if isinstance(val, str):
            val = _clean_numeric_string(val)
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return None


def apply_safe_decimal(df: pd.DataFrame, columns, as_float=False):
    """
    Convert specified columns to Decimal (or float if as_float=True).
    columns: str or list of str
    Returns: DataFrame (if multiple columns) or Series (if one column)
    """
    if isinstance(columns, str):
        columns = [columns]
    df = df.copy()
    def parse_val(val):
        try:
            d = safe_decimal(val)
            return float(d) if as_float and d is not None else d
        except (InvalidOperation, TypeError, ValueError):
            return float('nan') if as_float else Decimal("0.00")
    for col in columns:
        if col not in df.columns:
            logger.warning(f"[DecimalParse] Column {col} not found in DataFrame")
            df[col] = float('nan') if as_float else Decimal("0.00")
        else:
            df[col] = df[col].apply(parse_val)
    if len(columns) == 1:
        return df[columns[0]]
    return df[columns]


def validate_numeric_column(
    df: pd.DataFrame,
    column: str,
    sample_size: int = 5,
) -> list[str]:
    """
    Returns up to `sample_size` *raw* values that failed Decimal parsing.
    Useful for data-quality dashboards & unit tests.
    """
    if column not in df.columns:
        return []

    bad: list[str] = []
    for val in df[column].dropna().unique():
        if safe_decimal(val) == Decimal("0.00") and str(val).strip() not in {"0", "0.0"}:
            bad.append(str(val))
            if len(bad) == sample_size:
                break

    if bad:
        logger.warning(
            "[DecimalValidation] %d problematic values in %s: %s",
            len(bad),
            column,
            bad,
        )
    return bad
