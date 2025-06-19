import pandas as pd
import logging

log = logging.getLogger(__name__)


def get_income_trend(df: pd.DataFrame) -> list[dict]:
    """
    Returns daily income trend: jobs per day + income per day.
    Used by dashboard trend chart.

    Args:
        df (pd.DataFrame): DataFrame that has been enriched with date and total columns

    Returns:
        list[dict]: List of daily records with format:
            [{"date": "2025-06-01", "income": 1000.0, "jobs": 5}, ...]

    Note:
        - Requires 'date' and 'total' columns
        - Dates are resampled to daily frequency
        - Income is rounded to 2 decimal places
        - Jobs count is converted to integer
    """
    log.info("Computing income trend from DataFrame with %d rows", len(df))

    if df is None or df.empty:
        log.warning("Empty DataFrame provided to get_income_trend")
        return []

    if "date" not in df.columns or "total" not in df.columns:
        log.error(
            "Missing required columns: date=%s, total=%s",
            "date" in df.columns,
            "total" in df.columns,
        )
        return []

    try:
        # Group by date and compute metrics
        trend = (
            df.set_index("date")
            .resample("D")["total"]
            .agg(jobs=("size"), income=("sum"))
            .reset_index()
        )

        # Convert to list of dicts with proper formatting
        result = trend.to_dict(orient="records")
        for row in result:
            row["date"] = row["date"].strftime("%Y-%m-%d")
            row["income"] = float(round(row["income"], 2))
            row["jobs"] = int(row["jobs"])

        log.info("Successfully computed trend with %d daily records", len(result))
        return result

    except Exception as e:
        log.exception("Failed to compute income trend: %s", str(e))
        return []
