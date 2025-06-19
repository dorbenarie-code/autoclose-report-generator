from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path


def save_income_chart(daily_df: pd.DataFrame, out_path: Path) -> None:
    """
    Saves a bar chart of daily income to PNG.
    """
    log.debug("📊 Creating income chart from chart_utils.py")
    if "date" not in daily_df.columns or "income" not in daily_df.columns:
        raise ValueError("Missing 'date' or 'income' columns in daily_df.")

    if daily_df.empty:
        log.warning("No data provided for income chart.")
        return

    # Ensure 'date' is datetime64 for .dt usage
    if not pd.api.types.is_datetime64_any_dtype(daily_df["date"]):
        daily_df["date"] = pd.to_datetime(daily_df["date"], errors="coerce")

    plt.figure(figsize=(8, 4))
    plt.bar(daily_df["date"].dt.strftime("%Y-%m-%d"), daily_df["income"])
    plt.xticks(rotation=45, ha="right")
    plt.title("Daily Income")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
