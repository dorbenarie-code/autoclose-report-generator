import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from typing import Union
import logging

logger = logging.getLogger(__name__)

# ------------------------------
# 💡 Conversion Layer
# ------------------------------
def to_money(val: Union[str, float, int]) -> Decimal:
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as e:
        raise ValueError(f"Invalid value for money conversion: {val}") from e

def to_money_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="raise").apply(to_money)

# ------------------------------
# ✅ Validation Layer
# ------------------------------
def _validate_share(share: float) -> None:
    if not (0 < share < 1):
        raise ValueError(f"Invalid share: {share}. Must be between 0 and 1.")

def _validate_columns(df: pd.DataFrame, required: list[str]) -> None:
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        if df[col].isnull().any():
            raise ValueError(f"Column '{col}' contains NaN values")

# ------------------------------
# 🧠 Business Logic Layer
# ------------------------------
def _compute_profits(df: pd.DataFrame, share: float) -> pd.DataFrame:
    df["tech_profit"] = ((df["total"] - df["parts"]) * Decimal(str(share))).apply(to_money)
    df["balance_tech"] = (-df["tech_profit"]).apply(to_money)
    return df

# ------------------------------
# 🚀 Orchestration Layer
# ------------------------------
def enrich(df: pd.DataFrame, share: float = 0.5) -> pd.DataFrame:
    """
    Enrich the DataFrame with financial calculations.

    Steps:
      1. Validate that `share` is between 0 and 1.
      2. Ensure `total` column exists and has no NaN.
      3. Default missing `parts` column to zeros and validate.
      4. Convert `total` and `parts` to Decimal (2 decimal places).
      5. Compute:
         - tech_profit = (total - parts) * share
         - balance_tech = -tech_profit
      6. Log debug message with row count and share.

    Args:
        df: Input DataFrame containing at least `total` (and optional `parts`).
        share: Fraction of profit for the technician (0 < share < 1).

    Returns:
        A new DataFrame with added `tech_profit` and `balance_tech` columns.

    Raises:
        ValueError: On invalid share or missing/NaN columns.
    """
    _validate_share(share)
    _validate_columns(df, required=["total"])

    if "parts" not in df.columns:
        logger.warning("Column 'parts' not found – defaulting to 0")
        df["parts"] = 0
    _validate_columns(df, required=["parts"])

    df["total"] = to_money_series(df["total"])
    df["parts"] = to_money_series(df["parts"])

    df = _compute_profits(df, share)
    logger.debug(f"Enriched DataFrame with {len(df)} rows | share={share}")
    return df

# ------------------------------
# ➕ Totals Row Utility
# ------------------------------
def append_totals_row(df: pd.DataFrame, position: str = "top") -> pd.DataFrame:
    """
    Append a totals row to the DataFrame.

    Totals are computed for all numeric columns (including Decimal).
    The 'job_id' field (if exists) will be set to 'Totals:<row_count>'.

    Args:
        df: Input DataFrame (already enriched).
        position: "top" or "bottom" (where to place the totals row).

    Returns:
        DataFrame with totals row inserted.
    """
    if position not in ("top", "bottom"):
        raise ValueError(f"Invalid position: {position}")

    # Identify numeric columns, including Decimal
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, Decimal)).any()]
    totals = df[numeric_cols].sum(numeric_only=False)

    # Prepare totals row
    totals_row = totals.to_dict()
    if "job_id" in df.columns:
        totals_row["job_id"] = f"Totals:{len(df)}"

    # Ensure all columns are present in the totals row
    for col in df.columns:
        if col not in totals_row:
            totals_row[col] = None

    df_totals = pd.DataFrame([totals_row], columns=df.columns)

    # Concatenate totals row
    if position == "top":
        return pd.concat([df_totals, df], ignore_index=True)
    else:
        return pd.concat([df, df_totals], ignore_index=True)
