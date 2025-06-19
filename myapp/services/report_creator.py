from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from myapp.services.report_analyzer import build_report_data, get_report_summary
from myapp.services.pdf_generator import generate_pdf_report
from myapp.utils.export_utils import export_report_excel

# Constants for output directories; ensure these exist in your config
DEFAULT_REPORT_DIR = Path("static") / "client_reports"
DEFAULT_DATA_DIR = Path("output")

logger = log


def create_reports(
    excel_path: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    generate_personal: bool = True,
    generate_monthly: bool = True,
    report_dir: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> tuple[list[str], Optional[str], Optional[str]]:
    """
    Generate detailed PDF(s) and CSV/Excel summary from input Excel data.

    Args:
        excel_path: Path to the raw Excel file.
        start_date: Optional filter start.
        end_date: Optional filter end.
        generate_personal: If True, create one PDF per record.
        generate_monthly: If True, create a consolidated CSV and Excel summary.
        report_dir: Directory to save PDF reports.
        data_dir: Directory to save CSV/Excel data files.

    Returns:
        Tuple of (list of generated file names, path to CSV file, path to Excel file)
    """
    report_dir = report_dir or DEFAULT_REPORT_DIR
    data_dir = data_dir or DEFAULT_DATA_DIR

    # Ensure output directories exist
    report_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    generated_files: List[str] = []
    csv_path: Optional[str] = None
    excel_path_out: Optional[str] = None

    logger.info("🎯 Starting create_reports() for '%s'", excel_path)

    try:
        # 1. Analyze data
        detail_df, _ = build_report_data(
            excel_path, date_from=start_date, date_to=end_date
        )
        record_count = len(detail_df)
        if record_count == 0:
            logger.warning(
                "No records found after analysis. Aborting report generation."
            )
            return generated_files, csv_path, excel_path_out
        logger.info("✅ Data analyzed: %d records", record_count)

        logger.debug("TYPECHECK: %s in create_reports (detail_df)", type(detail_df).__name__)

        # 2. Personal PDFs
        if generate_personal:
            logger.info("📝 Generating personal PDF reports")
            for idx, record in enumerate(detail_df.to_dict(orient="records"), start=1):
                title = record.get("client_name", f"record_{idx}")
                pdf_filename = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = report_dir / pdf_filename
                try:
                    generate_pdf_report(df=pd.DataFrame([record]), title=title)
                    generated_files.append(pdf_filename)
                    logger.debug("Created personal PDF: %s", pdf_path)
                except Exception as ex:
                    logger.error(
                        "Failed to generate personal PDF for %s: %s", title, ex
                    )

        # 3. Monthly summary CSV & Excel
        if generate_monthly:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"report_{timestamp}.csv"
            excel_filename = f"report_{timestamp}.xlsx"
            csv_full = data_dir / csv_filename
            excel_full = data_dir / excel_filename

            try:
                detail_df.to_csv(csv_full, index=False)
                export_report_excel(detail_df)
                csv_path = str(csv_full)
                excel_path_out = str(excel_full)
                generated_files.extend([csv_filename, excel_filename])
                logger.info(
                    "✅ Summary CSV and Excel created: %s, %s", csv_full, excel_full
                )
            except Exception as ex:
                logger.error("Failed to export summary data: %s", ex)

    except Exception as e:
        logger.exception("❌ Failed create_reports overall: %s", e)
        raise RuntimeError(f"Report creation failed: {e}")

    logger.info("🏁 Completed create_reports(). Files: %s", generated_files)
    return generated_files, csv_path, excel_path_out
