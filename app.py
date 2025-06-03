# app.py
# 1. Imports
import os as system_os
import logging
from datetime import datetime, date
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from utils.ocr_utils import OCRProcessor
from utils.parsing_utils import parse_all_jobs, process_uploaded_file
from utils.report_utils import generate_excel_report, generate_pdf_report, generate_client_pdf, generate_monthly_summary_pdf
from utils.mail_utils import send_email_with_attachments
from utils.routes.reports import reports_bp
from routes.search_reports import search_bp
from routes.history_reports import history_bp
import pandas as pd
from utils.export_utils import export_monthly_summary_csv

# 2. Configuration & App Creation
UPLOAD_FOLDER = "uploads"
OUTPUT_ROOT = "output"
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".xlsx"}
system_os.makedirs(UPLOAD_FOLDER, exist_ok=True)
system_os.makedirs(OUTPUT_ROOT, exist_ok=True)
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_ROOT"] = OUTPUT_ROOT
app.register_blueprint(reports_bp)
app.register_blueprint(search_bp)
app.register_blueprint(history_bp)

# 3. Logging Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("AutoCloseApp")

# 4. Helper Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {ext.lstrip('.') for ext in ALLOWED_EXTENSIONS}


def parse_date(date_str: str) -> date:
    """
    Parse a date string in ISO format (YYYY-MM-DD) into a datetime.date object.
    Raises ValueError if the format is incorrect.
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def make_timestamped_filename(prefix: str, extension: str) -> str:
    """
    Create a standardized filename with a timestamp suffix, e.g., 'report_20250602T123456.xlsx'.
    """
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{prefix}_{ts}{extension}"


def filter_records_by_date(records: list, start_date: date, end_date: date) -> list:
    """
    Return only those job records whose 'date' field falls between start_date and end_date (inclusive).
    Skips records with missing or non-ISO dates.
    """
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


# --- פונקציה חדשה: יצירת דוחות ---
def create_reports(records, start_date, end_date, generate_personal, generate_monthly):
    import os
    from utils.report_utils import generate_client_pdf, generate_monthly_summary_pdf
    from utils.export_utils import export_monthly_summary_csv
    import pandas as pd
    generated_files = []
    csv_path = None
    csv_filename = None

    # בדיקת תקינות רשומות
    for i, rec in enumerate(records):
        if not rec.get("job_id") or not rec.get("tech"):
            logger.warning(f"Record #{i} missing job_id or tech: {rec}")

    # דוחות אישיים
    if generate_personal:
        for record in records:
            job_id = str(record.get("job_id", "unknown"))
            name = str(record.get("tech", "user")).split("/")[0].strip().replace(" ", "_")
            pdf_filename = secure_filename(f"{job_id}_{name}_{datetime.now():%Y%m%d%H%M%S}.pdf")
            output_path = os.path.join("output/client_reports", pdf_filename)
            try:
                generate_client_pdf(record, output_path)
                generated_files.append(pdf_filename)
                logger.info(f"Generated personal PDF: {pdf_filename}")
            except Exception as e:
                logger.error(f"PDF generation failed for {job_id}/{name}: {e}")

    # דוח חודשי
    if generate_monthly and records:
        df = pd.DataFrame(records)
        summary_filename = secure_filename(f"monthly_summary_{start_date}_to_{end_date}_{datetime.now():%Y%m%d%H%M%S}.pdf")
        summary_path = os.path.join("output/client_reports", summary_filename)
        try:
            generate_monthly_summary_pdf(records, summary_path, start_date, end_date)
            generated_files.append(summary_filename)
            logger.info(f"Generated monthly summary PDF: {summary_filename}")
        except Exception as e:
            logger.error(f"Failed to generate summary PDF: {e}")
        try:
            csv_path = export_monthly_summary_csv(df, start_date, end_date)
            csv_filename = os.path.basename(csv_path) if csv_path else None
            logger.info(f"CSV saved at: {csv_path}")
        except Exception as e:
            logger.error(f"Failed to generate summary CSV: {e}")

    return generated_files, csv_path, csv_filename


# 5. Routes
@app.route("/")
def index():
    return render_template("index.html", now=datetime.now())


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    free_text = request.form.get("free_text", "").strip()
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    # קריאת בחירת המשתמש מהטופס
    report_types = request.form.getlist("report_type")
    generate_personal = "personal" in report_types
    generate_monthly = "monthly" in report_types

    ALLOWED_EXTENSIONS = {'.txt', '.jpg', '.jpeg', '.png', '.xlsx', '.pdf'}

    def allowed_file(filename):
        return '.' in filename and system_os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

    records = []

    # קלט מקובץ
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = system_os.path.join("uploads", filename)
        file.save(file_path)
        try:
            records = process_uploaded_file(file_path, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            return render_template("errors/error_processing_failed.html", message=str(e))

    # קלט מטקסט חופשי
    elif free_text:
        from utils.free_text_parser import parse_free_text_block
        records = parse_free_text_block(free_text)

    # אם אין קלט תקין – שגיאה
    else:
        return render_template("errors/error_invalid_format.html")

    if not records:
        return render_template("errors/error_processing_failed.html", message="No job records in selected date range.")

    # --- יצירת דוחות ---
    system_os.makedirs("output/client_reports", exist_ok=True)
    generated_files, csv_path, csv_filename = create_reports(records, start_date, end_date, generate_personal, generate_monthly)

    # שם משתמש לתצוגה (אם יש)
    name = None
    if records:
        name = str(records[0].get("tech", "user")).split("/")[0].strip().replace(" ", "_")

    return render_template("success/upload_success.html",
                           user_name=name,
                           generated_filename=generated_files[0] if len(generated_files) == 1 else generated_files,
                           csv_path=csv_path,
                           csv_filename=csv_filename)


@app.route("/success")
def success_page():
    """
    Render the success page after a successful upload and report generation.
    Accepts optional query parameters:
    - pdf_url: link to the generated PDF
    - user_name: name of the user to greet
    """
    pdf_url = request.args.get("pdf_url")
    user_name = request.args.get("user_name")
    return render_template("success/upload_success.html", pdf_url=pdf_url, user_name=user_name)


@app.route('/download/<path:filename>')
def download_report(filename):
    return send_from_directory('output', filename, as_attachment=True)


# 6. Error Handlers
@app.errorhandler(400)
def bad_request(e):
    return render_template("errors/error_invalid_format.html"), 400


@app.errorhandler(403)
def forbidden_access(e):
    return render_template("errors/error_403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/error_404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("errors/error_processing_failed.html"), 500


# 7. Main Entrypoint
if __name__ == "__main__":
    app.run(debug=True, port=5000)
