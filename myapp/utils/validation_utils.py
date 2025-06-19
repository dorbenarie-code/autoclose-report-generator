# 📁 myapp/utils/validation_utils.py

import pandas as pd
import logging
from myapp.utils.decimal_utils import validate_numeric_column
from myapp.utils.date_utils import parse_date_flex

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "job_id", "technician", "created", "date", "closed",
    "job_type", "address", "total", "cash", "credit", "billing", "check",
    "tech_share", "tip_amount", "parts", "company_parts", "company",
]

NUMERIC_COLUMNS = ["total", "cash", "credit", "billing", "check", "tip_amount", "parts"]
DATE_COLUMNS = ["created", "date", "closed"]
PERCENT_COLUMNS = ["tech_share"]


def validate_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    logger.debug(f"[TYPECHECK] {__name__}.validate_uploaded_df → got {type(df).__name__} with shape {getattr(df, 'shape', 'N/A')}")
    logger.info("🚀 Starting validate_uploaded_df stage")
    validation_notes = None
    validated = True
    try:
        # 1. Required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            logger.error(f"[VALIDATION] Missing required columns: {missing}")
            validated = False
            validation_notes = f"Missing columns: {missing}"
            raise ValueError(f"Missing required columns: {missing}")

        # Exclude Totals rows for field-level validation
        df_filtered = df[~df["job_id"].astype(str).str.startswith("Totals")].copy()
        logger.debug("✅ Validating %d operational rows (excluding totals)", len(df_filtered))

        # 2. Numeric columns
        for col in NUMERIC_COLUMNS:
            try:
                validate_numeric_column(df_filtered, col)
            except Exception as e:
                logger.error(f"[VALIDATION] Numeric column error: {col}: {e}")
                validated = False
                validation_notes = f"Numeric column error: {col}: {e}"
                raise

        # 3. Percent columns
        for col in PERCENT_COLUMNS:
            if not df_filtered[col].astype(str).str.endswith("%").all():
                logger.error(f"[VALIDATION] Column {col} must contain percentage strings like '50%'")
                validated = False
                validation_notes = f"Column {col} must contain percentage strings like '50%'"
                raise ValueError(f"Column {col} must contain percentage strings like '50%'")

        # 4. Date columns
        for col in DATE_COLUMNS:
            try:
                df_filtered[col] = df_filtered[col].apply(parse_date_flex)
            except Exception as e:
                logger.error(f"[VALIDATION] Date column error: {col}: {e}")
                validated = False
                validation_notes = f"Date column error: {col}: {e}"
                raise

        # 5. Poisoned values
        bad_rows = df_filtered[
            df_filtered["total"].astype(str).str.contains(r"[^0-9.]") |
            df_filtered["tech_share"].astype(str).str.contains(r"[^0-9%]") |
            df_filtered["created"].astype(str).str.lower().isin(["n/a", "", "none"]) |
            df_filtered["date"].astype(str).str.lower().isin(["n/a", "", "none"]) |
            df_filtered["closed"].astype(str).str.lower().isin(["n/a", "", "none"])
        ]
        if not bad_rows.empty:
            logger.warning(f"[VALIDATION] Found {len(bad_rows)} suspicious rows: {bad_rows.index.tolist()}")
            validated = False
            validation_notes = f"Suspicious values in rows: {bad_rows.index.tolist()}"
            raise ValueError(f"Suspicious values in rows: {bad_rows.index.tolist()}")

        logger.info(f"✅ validate_uploaded_df complete → {df.shape}")
        return df
    except Exception as e:
        logger.exception(f"[ERROR] Failed inside validate_uploaded_df – {e}")
        logger.debug(f"[DF] Columns: {getattr(df, 'columns', [])}")
        logger.debug(f"[DF] Head:\n{getattr(df, 'head', lambda x=3: 'N/A')(3)}")
        raise
    finally:
        # Attach validation status for manifest
        df._autoclose_validation = dict(validated=validated, validation_notes=validation_notes)
