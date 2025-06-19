from myapp.utils.logger_config import get_logger
from myapp.config_shortcuts import EXPORT_DIR

log = get_logger(__name__)
import os
from datetime import datetime
from myapp.utils.logger_config import get_logger

logger = get_logger(__name__)


def list_exported_reports() -> list[dict[str, str]]:
    """
    Scans the EXPORT_DIR folder for PDF and Excel files,
    and returns a list of report info dicts, each containing:
        name, path, created date, type.
    The returned list is sorted by newest first (reverse chronological).

    Returns
    -------
    list of dict: Each dict has keys: name, path, created, type.
    """
    if not os.path.isdir(EXPORT_DIR):
        logger.warning(f"Export directory does not exist: {EXPORT_DIR}")
        return []

    reports = []
    try:
        # Sort by newest first
        filenames = sorted(os.listdir(EXPORT_DIR), reverse=True)
        for filename in filenames:
            if filename.endswith((".pdf", ".xlsx")):
                full_path = os.path.join(EXPORT_DIR, filename)
                # File creation/modified time
                created_at = datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d %H:%M")

                reports.append(
                    {
                        "name": filename,
                        "path": f"/download-report/{filename}",
                        "created": created_at,
                        "type": "PDF" if filename.endswith(".pdf") else "Excel",
                    }
                )
    except Exception as e:
        logger.error(f"Failed to list exported reports: {e}")

    return reports
