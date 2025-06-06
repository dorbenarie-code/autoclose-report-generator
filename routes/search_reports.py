# routes/search_reports.py

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, render_template, request, current_app

search_bp = Blueprint("search_reports", __name__)

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [SEARCH_REPORTS] %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@search_bp.route("/reports/search", methods=["GET", "POST"])
def search_reports() -> str:
    """
    Display a form to search report files by date range.
    On POST, return a list of matching report files from subfolders (YYYY-MM-DD).
    """
    output_root = Path(current_app.config["OUTPUT_ROOT"])
    results: List[Dict[str, Any]] = []
    error_message: str = ""

    if request.method == "POST":
        start_date_str = request.form.get("start_date", "").strip()
        end_date_str = request.form.get("end_date", "").strip()

        # Validate date inputs
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            error_message = "Invalid date format. Use YYYY-MM-DD."
            logger.warning(
                f"Date parsing failed: '{start_date_str}' to '{end_date_str}'"
            )
            return render_template(
                "search_reports.html", results=results, error=error_message
            )

        # Ensure root exists
        if not output_root.exists() or not output_root.is_dir():
            error_message = "Reports directory not found."
            logger.error(f"Output root missing: {output_root}")
            return render_template(
                "search_reports.html", results=results, error=error_message
            )

        # Iterate over date-named subfolders
        for folder in output_root.iterdir():
            if not folder.is_dir():
                continue

            try:
                folder_date = datetime.strptime(folder.name, "%Y-%m-%d").date()
            except ValueError:
                # Skip folders not matching YYYY-MM-DD
                continue

            if start_date <= folder_date <= end_date:
                for file in folder.iterdir():
                    if file.is_file() and file.suffix.lower() in {".xlsx", ".pdf"}:
                        results.append(
                            {
                                "date": folder.name,
                                "name": file.name,
                                "url": f"/{output_root.name}/{folder.name}/{file.name}",
                            }
                        )

        # Sort results by date then filename
        results.sort(key=lambda r: (r["date"], r["name"]))

    return render_template("search_reports.html", results=results, error=error_message)
