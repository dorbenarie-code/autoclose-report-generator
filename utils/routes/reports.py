# routes/reports.py

# === Standard Library Imports ===
import os
import logging
from pathlib import Path
from typing import cast

# === Third-Party Imports ===
from flask import (
    Blueprint,
    request,
    redirect,
    flash,
    render_template,
    current_app,
    Response,
)

# === Internal/Project Imports ===
from services.email_service import EmailService

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
def list_reports() -> str:
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
                folders.append(
                    {
                        "date": dir_path.name,
                        "files": files,
                        "url_path": f"/{output_root}/{dir_path.name}",
                    }
                )

    return render_template("reports.html", folders=folders)


@reports_bp.route("/reports/<date_str>")
def reports_by_date(date_str: str) -> str:
    """
    מציג את כל העבודות (jobs) עבור תאריך מסוים (YYYY-MM-DD) בטבלה.
    """
    from utils.report_utils import get_jobs_by_date

    jobs = get_jobs_by_date(date_str)  # פונקציה שתחזיר רשימת dict של עבודות
    return render_template("reports_by_date.html", date=date_str, jobs=jobs)


@reports_bp.route("/send-monthly-report", methods=["POST"])
def send_monthly_report() -> Response:
    """
    Handle form submission to send a monthly report PDF via email.
    Expects 'start_date', 'end_date', and optional 'email' in the POST form.
    """
    try:
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        email = request.form.get("email", "").strip()

        # Ensure both dates are provided
        if not start_date or not end_date:
            flash("Start and end dates are required.", "danger")
            return cast(Response, redirect(request.referrer))

        # Build the path to the PDF file
        pdf_filename = f"monthly_summary_{start_date}_{end_date}.pdf"
        pdf_path = os.path.join("static", "monthly_reports", pdf_filename)

        # Check if the PDF file exists before sending
        if not os.path.isfile(pdf_path):
            logging.error(f"PDF file not found: {pdf_path}")
            flash("❌ Report file not found on server.", "danger")
            return cast(Response, redirect(request.referrer))

        # Create the email service and send the report
        service = EmailService()
        success = service.send_monthly_report(
            pdf_path=pdf_path,
            start_date=start_date,
            end_date=end_date,
            recipient=email or None,
        )

        if success:
            flash("✅ Monthly report sent successfully.", "success")
        else:
            flash("❌ Failed to send report. Please check logs.", "danger")

        return cast(Response, redirect(request.referrer))

    except Exception:
        logging.exception("Unexpected error in send_monthly_report endpoint")
        flash("❌ Unexpected error during email sending.", "danger")
        return cast(Response, redirect(request.referrer))
