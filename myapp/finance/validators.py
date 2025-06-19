from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
import numpy as np
import pandas as pd


def run_sanity_checks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns only rows that violate one or more financial rules.
    Adds a column 'failed_rules' with comma-separated reasons.
    """
    rules = {
        "NEGATIVE_PROFIT": df["company_net"] < 0,
        "PARTS_EXCEED_TOTAL": df["parts"] > df["total"],
        "EXCESSIVE_COMMISSION": (df["total"] > 0)
        & (df["tech_cut"] / df["total"] > 0.9),
    }

    # Combine masks
    mask = np.logical_or.reduce(list(rules.values()))
    flagged_rows = df.loc[mask].copy()

    # Build list of failed rule names for each row
    failed_cols = pd.concat(
        [pd.Series(name, index=cond.index).where(cond) for name, cond in rules.items()],
        axis=1,
    )

    flagged_rows["failed_rules"] = failed_cols.apply(
        lambda row: ",".join(row.dropna()), axis=1
    )

    return flagged_rows
