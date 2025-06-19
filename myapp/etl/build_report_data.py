from myapp.utils.logger_config import get_logger
from pandas import DataFrame

log = get_logger(__name__)

import pandas as pd
from typing import Union, Optional, Tuple, Any
from datetime import datetime
from myapp.utils.column_mapper import load_column_schema
from myapp.utils.parsers import parse_dates_in_columns


def build_report_data(
    df_or_path: Union[pd.DataFrame, str],
    schema_name: str = "default",
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Load and clean data, apply filters, return cleaned df and summary.
    """

    # Step 1: Load input
    if isinstance(df_or_path, str):
        log.info(f"📥 Reading Excel from: {df_or_path}")
        df = pd.read_excel(df_or_path)
    else:
        df = df_or_path.copy()

    log.info(f"🔢 Loaded {len(df)} rows before cleaning")

    # Step 2: Load schema
    schema = load_column_schema(schema_name)
    column_map = schema.get("raw_to_canonical", {})
    required_cols = schema.get("required_columns", [])
    date_cols = schema.get("date_columns", [])

    # Step 3: Rename columns
    df = df.rename(columns=lambda col: column_map.get(col.strip(), col.strip()))

    # Step 4: Validate required columns
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        log.error(f"❌ Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")

    # Step 5: Drop empty rows
    df.dropna(how="all", inplace=True)

    # Step 6: Parse date columns
    df = parse_dates_in_columns(df, date_cols)

    # Step 7: Apply filters
    if tech_filter:
        df = df[df["tech"].isin(tech_filter)]
    if service_filter:
        df = df[df["job_type"].isin(service_filter)]
    if date_from:
        df = df[df["date"] >= date_from]
    if date_to:
        df = df[df["date"] <= date_to]

    log.info(f"✅ Rows after filtering: {len(df)}")

    # Step 8: Clean string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    print("📊 עמודות DF לפני סיכום:", df.columns.tolist())
    summary = {
        "rows_after_cleaning": len(df),
        "columns": list(df.columns),
    }

    return df, summary


def build_df_for_insights(*args: Any, **kwargs: Any) -> DataFrame:
    return DataFrame()  # Dummy until implementation
