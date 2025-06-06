# app.py

# --- Built-in ---
import logging
import os
from datetime import date, datetime
from typing import Optional, Any, Tuple

# --- Third-party ---
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename

# --- Internal Imports ---
from routes.history_reports import history_bp
from routes.search_reports import search_bp
from utils.export_utils import export_monthly_summary_csv
from utils.free_text_parser import parse_free_text_block
from utils.parsing_utils import process_uploaded_file
from utils.report_utils import (
    generate_client_pdf,
    generate_monthly_summary_pdf,
)
from utils.routes.reports import reports_bp

# --- Configuration ---
UPLOAD_FOLDER = "uploads"
OUTPUT_ROOT = "output"
CLIENT_REPORTS_FOLDER = os.path.join("static", "client_reports")
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".xlsx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIENT_REPORTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_ROOT"] = OUTPUT_ROOT
app.register_blueprint(reports_bp)
app.register_blueprint(search_bp)
app.register_blueprint(history_bp)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("AutoCloseApp")


# --- Helper Functions ---
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        ext.lstrip(".") for ext in ALLOWED_EXTENSIONS
    }


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def make_timestamped_filename(prefix: str, extension: str) -> str:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{prefix}_{ts}{extension}"


def filter_records_by_date(
    records: list[dict[str, Any]], start_date: date, end_date: date
) -> list[dict[str, Any]]:
    filtered = []
    for rec in records:
        rec_date_str = rec.get("date")
        if not rec_date_str or rec_date_str == "Unknown":
            continue
        try:
            rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
            if start_date <= rec_date <= end_date:
                filtered.append(rec)
        except ValueError:
            continue
    return filtered


def create_reports(
    records: list[dict[str, Any]],
    start_date: Optional[date],
    end_date: Optional[date],
    generate_personal: bool,
    generate_monthly: bool,
) -> tuple[list[str], Optional[str], Optional[str]]:
    # הגנה על פורמט תאריכים
    if isinstance(start_date, date):
        start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date_str = str(start_date)

    if isinstance(end_date, date):
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date_str = str(end_date)

    generated_files = []
    csv_path = None
    csv_filename = None

    # בדיקת רשומות חסרות
    for i, rec in enumerate(records):
        if not rec.get("job_id") or not rec.get("tech"):
            logger.warning(f"Record #{i} missing job_id or tech: {rec}")

    # ניטור דוחות אישיים
    if generate_personal:
        for record in records:
            job_id = str(record.get("job_id", "unknown"))
            name = (
                str(record.get("tech", "user")).split("/")[0].strip().replace(" ", "_")
            )
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            pdf_filename = secure_filename(f"{job_id}_{name}_{timestamp}.pdf")
            output_path = os.path.join(CLIENT_REPORTS_FOLDER, pdf_filename)
            try:
                generate_client_pdf(record, output_path)
                generated_files.append(pdf_filename)
                logger.info(f"Generated personal PDF: {pdf_filename}")
            except Exception as e:
                logger.error("PDF generation failed for %s/%s: %s", job_id, name, e)

    # דוחות חודשיים ו־CSV
    if generate_monthly and records:
        df = pd.DataFrame(records)
        summary_name = f"monthly_summary_{start_date_str}_to_{end_date_str}"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        summary_pdf = secure_filename(f"{summary_name}_{timestamp}.pdf")
        try:
            if start_date is not None and end_date is not None:
                generate_monthly_summary_pdf(records, start_date, end_date)
                generated_files.append(summary_pdf)
                logger.info(f"Generated monthly summary PDF: {summary_pdf}")
            else:
                logger.error(
                    "start_date or end_date is None for monthly summary PDF generation."
                )
        except Exception as e:
            logger.error("Failed to generate summary PDF: %s", e)

        try:
            # export_monthly_summary_csv מצפה ל-str | date | datetime
            start_csv = start_date if start_date is not None else ""
            end_csv = end_date if end_date is not None else ""
            csv_path = export_monthly_summary_csv(df, start_csv, end_csv)
            csv_filename = os.path.basename(csv_path) if csv_path else None
            logger.info(f"CSV saved at: {csv_path}")
        except Exception as e:
            logger.error("Failed to generate summary CSV: %s", e)

    return generated_files, csv_path, csv_filename


# --- Routes ---
@app.route("/")
def index() -> str:
    # הצגת קבצים קיימים להורדה
    file_list = []
    try:
        file_list = [
            f
            for f in os.listdir(CLIENT_REPORTS_FOLDER)
            if os.path.isfile(os.path.join(CLIENT_REPORTS_FOLDER, f))
        ]
        file_list.sort(reverse=True)
    except Exception:
        file_list = []
    return render_template("index.html", now=datetime.now(), file_list=file_list)


@app.route("/upload", methods=["POST"])
def upload() -> str:
    file = request.files.get("file")
    free_text = request.form.get("free_text", "").strip()
    start_input = request.form.get("start_date")
    end_input = request.form.get("end_date")

    try:
        start_date = parse_date(start_input) if start_input else None
        end_date = parse_date(end_input) if end_input else None
    except ValueError as e:
        return render_template("errors/error_invalid_format.html", message=str(e))

    report_types = request.form.getlist("report_type")
    generate_personal = "personal" in report_types
    generate_monthly = "monthly" in report_types

    records: list[dict[str, Any]] = []

    if file and file.filename is not None and allowed_file(str(file.filename)):
        filename = secure_filename(str(file.filename))
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        try:
            # process_uploaded_file מצפה ל-str, לא ל-date
            start_str = start_date.strftime("%Y-%m-%d") if start_date else ""
            end_str = end_date.strftime("%Y-%m-%d") if end_date else ""
            records = process_uploaded_file(file_path, start_str, end_str)
        except Exception as e:
            logger.error("Failed to process file: %s", e)
            return render_template(
                "errors/error_processing_failed.html", message=str(e)
            )

    elif free_text:
        try:
            records = parse_free_text_block(free_text)
            # filter_records_by_date מצפה ל-date, לא ל-None
            if start_date is not None and end_date is not None:
                records = filter_records_by_date(records, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to parse free text: {e}")
            return render_template(
                "errors/error_processing_failed.html", message=str(e)
            )
        else:
            if not records:
                return render_template(
                    "errors/error_processing_failed.html",
                    message="No job records in selected date range.",
                )

    generated_files, csv_path, csv_filename = create_reports(
        records, start_date, end_date, generate_personal, generate_monthly
    )

    name: Optional[str] = None
    if records:
        name = (
            str(records[0].get("tech", "user")).split("/")[0].strip().replace(" ", "_")
        )

    return render_template(
        "success/upload_success.html",
        user_name=name,
        generated_filename=(
            generated_files[0] if len(generated_files) == 1 else generated_files
        ),
        csv_path=csv_path,
        csv_filename=csv_filename,
    )


@app.route("/success")
def success_page() -> str:
    pdf_url = request.args.get("pdf_url")
    user_name = request.args.get("user_name")
    return render_template(
        "success/upload_success.html", pdf_url=pdf_url, user_name=user_name
    )


@app.route("/download/<filename>")
def download_file(filename: str) -> Any:
    return send_from_directory(CLIENT_REPORTS_FOLDER, filename)


# --- Error Handlers ---
@app.errorhandler(400)
def bad_request(e: Exception) -> Tuple[str, int]:
    return render_template("errors/error_invalid_format.html"), 400


@app.errorhandler(403)
def forbidden_access(e: Exception) -> Tuple[str, int]:
    return render_template("errors/error_403.html"), 403


@app.errorhandler(404)
def page_not_found(e: Exception) -> Tuple[str, int]:
    return render_template("errors/error_404.html"), 404


@app.errorhandler(500)
def internal_error(e: Exception) -> Tuple[str, int]:
    return render_template("errors/error_processing_failed.html"), 500


# --- Main Entrypoint (for local dev only) ---
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
