from pathlib import Path
import pandas as pd
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

def safe_sum_decimal(series: pd.Series) -> Decimal:
    total = Decimal("0.00")
    for val in series.dropna():
        try:
            total += Decimal(str(val))
        except (InvalidOperation, TypeError):
            continue
    return total

def validate_report_integrity(
    report_path: Path,
    df: pd.DataFrame,
    *,
    totals_label: str = "Totals:",
    min_pdf_size: int = 10_000
) -> None:
    """
    Validate that a generated PDF report and its source DataFrame meet integrity standards.

    Performs these checks:
    1. PDF file exists at `report_path`.
    2. PDF file size is at least `min_pdf_size` bytes.
    3. DataFrame contains meaningful data rows beyond any totals row.
    4. 'total' column exists and its sum is positive.

    Parameters
    ----------
    report_path : Path
        Path to the generated PDF report.
    df : pd.DataFrame
        Data used to generate the report; may include a leading totals row.
    totals_label : str, optional
        Identifier prefix for a totals row in 'job_id', by default "Totals:".
    min_pdf_size : int, optional
        Minimum PDF file size in bytes (default 10_000).

    Raises
    ------
    ValueError
        If any validation step fails.
    """
    logger.debug(f"🔍 Validating PDF integrity: {report_path.name}")
    # Step 1: Ensure PDF exists
    if not report_path.is_file():
        logger.error("PDF report not found: %s", report_path)
        raise ValueError(f"PDF report not found: {report_path}")

    # Step 2: Verify file size is reasonable
    size = report_path.stat().st_size
    if size < min_pdf_size:
        logger.warning(
            "Generated PDF is too small: %s (%d bytes)", report_path, size
        )
        raise ValueError("Generated PDF seems incomplete or corrupt.")

    # Step 3: Check for meaningful data rows (exclude totals)
    row_count = len(df)
    if "job_id" in df.columns:
        first_val = df.iloc[0]["job_id"]
        if isinstance(first_val, str) and first_val.startswith(totals_label):
            row_count -= 1
    if row_count <= 0:
        logger.warning(
            "Report has insufficient data rows (only totals?): %s", report_path
        )
        raise ValueError("Report contains no meaningful data.")

    # Step 4: Confirm total sum is positive
    if "total" not in df.columns:
        logger.error(
            "'total' column missing in DataFrame for report validation."
        )
        raise ValueError("Missing 'total' column in report data.")
    total_sum = safe_sum_decimal(df["total"])
    if total_sum <= 0:
        logger.warning(
            "Report total sum is non-positive: %.2f", total_sum
        )
        raise ValueError("Report total is zero or negative.")

    logger.info(
        "Report validation passed for %s (rows: %d, total: %.2f, size: %d bytes)",
        report_path,
        row_count,
        total_sum,
        size
    ) 