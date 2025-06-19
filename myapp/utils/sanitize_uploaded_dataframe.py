import pandas as pd
from myapp.utils.logger_config import get_logger

logger = get_logger(__name__)

def sanitize_uploaded_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes clearly invalid rows based on date-related columns only.
    """
    logger.debug("TYPECHECK: %s in sanitize_uploaded_dataframe", type(df).__name__)
    bad_values = {"total", "totals", "billing", "nan", "0", "", "date"}
    date_columns = ["date", "closed", "created_at", "updated_at"]

    def is_bad(val):
        s = str(val).strip().lower()
        return s in bad_values or ("Unnamed" in s)

    for col in date_columns:
        if col in df.columns:
            df = df[~df[col].apply(is_bad)]

    return df
