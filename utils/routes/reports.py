# routes/reports.py

import os
from pathlib import Path
from flask import Blueprint, render_template, current_app, abort
from typing import List

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
def list_reports():
    """
    List all report directories (YYYY-MM-DD) and their .xlsx/.pdf files
    from the OUTPUT_ROOT. Passes a list of dicts to the template, each with:
      - date: directory name (string)
      - files: list of filenames in that directory
      - url_path: URL path segment to reach those files
    """
    output_root = current_app.config["OUTPUT_ROOT"]
    root_path = Path(output_root)
    folders = []

    if root_path.exists() and root_path.is_dir():
        # Sort directory names in reverse (newest first)
        for dir_path in sorted(root_path.iterdir(), key=lambda p: p.name, reverse=True):
            if not dir_path.is_dir():
                continue

            # Collect .xlsx and .pdf files in this date folder
            files = [
                f.name
                for f in sorted(dir_path.iterdir())
                if f.is_file() and f.suffix.lower() in {".xlsx", ".pdf"}
            ]

            if files:
                folders.append({
                    "date": dir_path.name,
                    "files": files,
                    "url_path": f"/{output_root}/{dir_path.name}"
                })

    return render_template("reports.html", folders=folders)


@reports_bp.route("/reports/<date_str>")
def reports_by_date(date_str: str):
    """
    מציג את כל העבודות (jobs) עבור תאריך מסוים (YYYY-MM-DD) בטבלה.
    """
    from utils.report_utils import get_jobs_by_date
    jobs = get_jobs_by_date(date_str)  # פונקציה שתחזיר רשימת dict של עבודות
    return render_template(
        "reports_by_date.html",
        date=date_str,
        jobs=jobs
    )
