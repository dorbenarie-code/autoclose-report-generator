# data_loader.py

import os
from typing import Set, List, Tuple, Optional, Any
import pandas as pd
from pathlib import Path
import re
import logging
from myapp.utils.file_validator import load_and_clean_data

logger = logging.getLogger("AutoCloseDashboard")


def get_kpi_metrics(filepath: str = "output/merged_jobs.csv") -> Tuple[int, int, float]:
    """
    Returns basic KPI metrics: total reports, active technicians, and total amount.
    """
    try:
        df = load_and_clean_data(filepath)
        total_reports = len(df)
        active_technicians = (
            df["technician"].nunique() if "technician" in df.columns else 0
        )
        total_amount = df["amount"].sum() if "amount" in df.columns else 0.0
        return total_reports, active_technicians, total_amount
    except Exception as e:
        logger.error(f"[ERROR] Failed to load KPIs: {e}")
        return 0, 0, 0


def load_dashboard_data(path: str = "output/merged_jobs.csv") -> pd.DataFrame:
    """
    Loads dashboard data from CSV. Returns a partially usable DataFrame if optional columns are missing,
    without raising hard errors (except for truly critical failures, like file not found).

    Fallback Behavior:
    - If file is missing or can't be read -> returns empty DataFrame.
    - If 'date' is missing or parsing fails -> sets df["date"] to NaT and logs a warning.
    - If optional columns like 'technician'/'job_type' are missing -> adds them as empty columns (pd.NA),
      so the dashboard won't crash when referencing them.
    """

    # Case 1: File does not exist
    if not os.path.isfile(path):
        logger.error(f"Dashboard data file not found: {path}")
        return pd.DataFrame()  # Return empty DataFrame safely

    # Case 2: Could not read CSV at all
    try:
        df = load_and_clean_data(path)  # your existing data load + cleanup logic
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return pd.DataFrame()

    # Case 3: Parse 'date' column
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        except Exception as e:
            logger.warning(f"Could not convert 'date' column: {e}")
            df["date"] = pd.NaT
    else:
        logger.warning(
            "[WARNING] 'date' column missing – dashboard graphs may be limited."
        )
        df["date"] = pd.NaT

    # Case 4: Ensure optional columns exist, even if empty
    # So referencing df["technician"] or df["job_type"] won't crash downstream
    optional_cols = ["technician", "job_type"]
    for col in optional_cols:
        if col not in df.columns:
            logger.warning(
                f"[DASHBOARD] Column '{col}' missing – related features may not work."
            )
            df[col] = pd.NA

    return df


def get_available_report_ranges(
    folder: str = "static/monthly_reports",
) -> List[Tuple[str, str]]:
    """
    Returns a list of (start_date, end_date) tuples for which monthly summary PDFs exist.
    File format assumed: monthly_summary_YYYY-MM-DD_to_YYYY-MM-DD.pdf
    """
    result = []
    path = Path(folder)
    if not path.exists():
        return []

    pattern = re.compile(
        r"monthly_summary_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})\.pdf"
    )
    for f in path.glob("*.pdf"):
        match = pattern.match(f.name)
        if match:
            start_date, end_date = match.groups()
            result.append((start_date, end_date))

    return sorted(result, reverse=True)


def get_filter_options(
    filepath: str = "output/merged_jobs.csv",
) -> Tuple[List[dict[str, Any]], List[dict[str, Any]]]:
    """
    Extracts dropdown options from the data for technician and report_type.

    Args:
        filepath (str): Path to the CSV file. Defaults to "output/merged_jobs.csv".

    Returns:
        tuple: (technician_options, report_type_options)
               Each is a list of dicts with "label" and "value".
    """
    try:
        df = load_and_clean_data(filepath)

        # טכנאים
        if "technician" in df.columns:
            tech_series = df["technician"].dropna().unique()
            tech_options = [{"label": t, "value": t} for t in sorted(tech_series)]
        else:
            tech_options = []

        # סוגי דוחות (job_type)
        if "job_type" in df.columns:
            job_series = df["job_type"].dropna().unique()
            report_options = [{"label": r, "value": r} for r in sorted(job_series)]
        else:
            report_options = []

        return tech_options, report_options

    except Exception as e:
        logger.error(f"[ERROR] Failed to load filter options: {e}")
        return [], []


def load_kpi_data() -> Tuple[int, int, float]:
    """
    Loads KPI metrics from 'output/merged_jobs.csv'.

    Returns
    -------
    tuple (int, int, float)
        (total_reports, active_technicians, total_amount)
    """
    try:
        df = load_and_clean_data("output/merged_jobs.csv")

        total_reports = len(df)
        active_technicians = (
            df["technician"].nunique() if "technician" in df.columns else 0
        )

        # If 'price' column is missing, use 0.0
        total_amount = df["price"].sum() if "price" in df.columns else 0.0

        return total_reports, active_technicians, total_amount

    except Exception as e:
        logger.exception("Failed to load KPI data")
        return 0, 0, 0.0


# Allow running directly from file for testing/debugging
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))

    try:
        df = load_and_clean_data("uploads/good_test_data.csv")
        print(df.head())
    except Exception as e:
        print(f"Error: {e}")
