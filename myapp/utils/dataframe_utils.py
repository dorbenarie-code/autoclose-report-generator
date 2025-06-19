__all__ = [
    "enrich",
    "coerce_dates",
    "append_totals_row",
    "format_currency_columns",
    "safe_cast_columns",
    "validate_schema",
    "format_report_columns",
    "prepare_pdf_dataframe",
]

from pandas import DataFrame
import pandas as pd
import numpy as np
from decimal import Decimal
from typing import Union

# —————————————————————————————————————————————————————————————————
# Financial enrichment: computes tech_profit, balance_tech
# —————————————————————————————————————————————————————————————————
from myapp.utils.calculations import enrich as enrich_calc

def enrich(df: DataFrame, share: Union[str, float] = 0.5) -> DataFrame:
    """
    Enrich the DataFrame with financial calculations.

    Args:
        df: Input DataFrame with 'total' and optional 'parts'.
        share: Technician share as float (0<share<=1) or percentage string '50%'.

    Returns:
        DataFrame with added 'tech_share', 'tech_profit', 'balance_tech'.

    Raises:
        ValueError: On invalid share or missing 'total' column.
    """
    out = df.copy()
    # parse share
    if isinstance(share, str):
        if share.endswith('%'):
            share_val = float(share.rstrip('%')) / 100.0
        else:
            share_val = float(share)
    else:
        share_val = float(share)
    if not (0 < share_val <= 1):
        raise ValueError("share must be between 0 and 1 (or '100%')")
    # ensure 'total'
    if 'total' not in out.columns:
        raise ValueError("Missing required column 'total'")
    # fill parts
    out['parts'] = out.get('parts', pd.Series([0]*len(out))).fillna(0).astype(float)
    # compute
    out['tech_share'] = f"{int(share_val*100)}%"
    out['tech_profit'] = ((out['total'] - out['parts']) * share_val).round(2)
    out['balance_tech'] = (-(out['tech_profit'])).round(2)
    return out

# —————————————————————————————————————————————————————————————————
# Date coercion
# —————————————————————————————————————————————————————————————————
def coerce_dates(df: DataFrame, cols: list[str]) -> DataFrame:
    """
    Coerce the given list of date-columns to datetime64.
    """
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out

# —————————————————————————————————————————————————————————————————
# PDF preparation helpers
# —————————————————————————————————————————————————————————————————
def append_totals_row(df: DataFrame, position: str = "top") -> DataFrame:
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
    if df.empty:
        return df
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        return df
    totals = {col: df[col].apply(lambda v: Decimal(str(v))).sum() for col in numeric_cols}
    total_row = {c: None for c in df.columns}
    total_row["job_id"] = f"Totals:{len(df)}"
    for col in numeric_cols:
        total_row[col] = totals[col]
    total_df = pd.DataFrame([total_row])
    if position == "top":
        result = pd.concat([total_df, df], ignore_index=True)
    else:
        result = pd.concat([df, total_df], ignore_index=True)
    return result


def format_currency_columns(df: DataFrame, cols: list[str]) -> DataFrame:
    """
    Format numeric columns as strings with comma thousand separators, two decimals.
    Raises:
        ValueError: if any column not found.
    """
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            raise ValueError(f"Column '{col}' not found for formatting")
        def fmt(x):
            if pd.isna(x):
                return ""
            return f"{float(x):,.2f}"
        out[col] = out[col].apply(fmt)
    return out


def safe_cast_columns(df: DataFrame, mapping: dict[str, type]) -> DataFrame:
    """
    Cast specified columns to given types.

    Raises:
        ValueError: if column not found or cast fails.
    """
    out = df.copy()
    for col, target in mapping.items():
        if col not in out.columns:
            raise ValueError(f"Column '{col}' not found")
        try:
            out[col] = out[col].apply(lambda v: target(v) if pd.notna(v) else v)
        except Exception:
            raise ValueError(f"Failed to cast column '{col}'")
    return out


def validate_schema(df: DataFrame, schema: dict[str, Union[type, callable]] = None) -> None:
    """
    Validate DataFrame schema: column presence and types or callables.

    Raises:
        ValueError: on missing columns or invalid values.
    """
    if schema is None:
        required = ['job_id', 'total', 'parts']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")
        return
    # check presence
    missing = [c for c in schema if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    # check types/validators
    for col, rule in schema.items():
        vals = df[col]
        if isinstance(rule, type):
            invalid = [v for v in vals if pd.notna(v) and not isinstance(v, rule)]
            if invalid:
                raise ValueError(f"invalid values in column '{col}'")
        elif callable(rule):
            invalid = [v for v in vals if not rule(v)]
            if invalid:
                raise ValueError("invalid values")
    return


def format_report_columns(df: DataFrame) -> DataFrame:
    """
    Format all currency columns as strings with comma thousand separators and two decimals.
    Applies to: total, parts, tech_cut, company_net (if present).
    """
    currency_cols = [col for col in ["total", "parts", "tech_cut", "company_net"] if col in df.columns]
    if currency_cols:
        return format_currency_columns(df, currency_cols)
    return df


def prepare_pdf_dataframe(df: DataFrame) -> DataFrame:
    """
    Pipeline for preparing DataFrame for PDF output.
    """
    out = df.copy()
    out = coerce_dates(out)
    out = enrich(out)
    out = append_totals_row(out)
    out = format_report_columns(out)
    return out

def enrich_financials(df: DataFrame) -> DataFrame:
    """
    Enrich a raw financial DataFrame with calculated fields and flags, ensuring data integrity.
    ...
    """
    required_cols = {"total", "parts", "tech_share", "date", "closed"}
    needed_cols = [
        "net_income", "tech_cut", "company_net", "duration_min",
        "parts_flag", "net_flag", "commission_flag", "duration_flag", "flags"
    ]
    missing = required_cols - set(df.columns)
    out = df.copy()
    if missing:
        for col in needed_cols:
            if col not in out.columns:
                out[col] = None
        return out
    enriched = df.copy()
    enriched["parts"] = enriched["parts"].fillna(0).astype(float)
    enriched["total"] = enriched["total"].fillna(0).astype(float)
    enriched["tech_share"] = (
        enriched["tech_share"]
        .str.rstrip("%")
        .astype(float)
        .div(100)
        .round(3)
    )
    if enriched["tech_share"].max() > 1:
        raise ValueError("tech_share must be <= 100% (1.0)")
    enriched["net_income"] = enriched["total"] - enriched["parts"]
    enriched["tech_cut"] = (enriched["total"] * enriched["tech_share"]).round(2)
    enriched["company_net"] = (enriched["net_income"] - enriched["tech_cut"]).round(2)
    enriched["duration_min"] = (
        pd.to_datetime(enriched["closed"], errors="coerce")
        .sub(pd.to_datetime(enriched["date"], errors="coerce"))
        .dt.total_seconds()
        .div(60)
        .round(1)
    )
    flags_definitions = {
        "parts_flag": np.where(enriched["parts"] > enriched["total"], "PARTS>PRICE", ""),
        "net_flag": np.where(enriched["company_net"] < 0, "NEGATIVE", ""),
        "commission_flag": np.where(
            (enriched["total"] > 0) & (enriched["tech_cut"].div(enriched["total"]) > 0.8),
            "HIGH",
            ""
        ),
        "duration_flag": np.where(enriched["duration_min"].isna(), "NO_END", ""),
    }
    for flag_col, flag_vals in flags_definitions.items():
        enriched[flag_col] = flag_vals
    enriched["flags"] = (
        enriched[list(flags_definitions.keys())]
        .apply(lambda row: ",".join([f for f in row if f]), axis=1)
    )
    enriched["net_income"] = enriched["net_income"].round(2)
    return enriched
