# app.py

# --- Built-in ---
import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional, Any, Tuple, Dict, List, cast
from pathlib import Path
from functools import wraps

# --- Third-party ---
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    flash,
    redirect,
    url_for,
    session,
    current_app as app,
    Response,
    make_response,
    jsonify,
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Sentry Integration ---
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()]
    )

# --- Internal Imports ---
from myapp.routes.history_reports import history_bp
from myapp.routes.search_reports import search_bp
from myapp.routes.api_reports import api_reports_bp
from myapp.routes.download_reports import download_bp
from myapp.utils.export_utils import export_monthly_summary_csv

from myapp.utils.logger_config import get_logger, init_logging

log = get_logger(__name__)

try:
    from myapp.utils.free_text_parser import parse_free_text_block
except ImportError as e:
    logging.getLogger(__name__).error(
        f"[IMPORT ERROR] Failed to import parse_free_text_block: {e}"
    )
    log.error(f"[IMPORT ERROR] Failed to import parse_free_text_block: {e}")


from myapp.utils.parsers import parse_date, filter_records_by_date
from myapp.utils.report_utils import generate_client_pdf, generate_monthly_summary_pdf
from myapp.routes.reports import reports_bp
from myapp.utils.xls_converter import XlsConverter
from myapp.error_handler.base import FileFormatError
from myapp.routes.upload_reports import upload_bp
from myapp.dashboard.interactive_dashboard import create_dashboard
from myapp.dashboard.data_loader import get_available_report_ranges
from scripts.auto_run import auto_run
from myapp.dashboard.callbacks.dashboard_callbacks import register_callbacks
from myapp.routes.report_routes import report_bp
from myapp.services import report_analyzer
from myapp.services.pdf_generator import generate_pdf_report
from myapp.utils.export_utils import export_report_excel
from myapp.finance.validators import run_sanity_checks
from myapp.services.email_service import EmailService
from myapp.utils.chart_utils import save_income_chart
from myapp.routes.admin_rules import admin_bp
from myapp.routes.api_insights import api_insights_bp
from myapp.routes.api_tasks import api_tasks_bp
from myapp.services.response_utils import handle_exception_context
from myapp.etl.build_report_data import build_report_data
from myapp.utils.date_utils import parse_date_flex
from myapp.routes.health import health_bp
from myapp.routes.auth import auth_bp


# --- Logging Setup ---
log_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

file_handler = logging.FileHandler(
    "auto_close.log", mode="w"
)  # 'w' to rewrite on each run
file_handler.setFormatter(log_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

log.setLevel(logging.INFO)
log.addHandler(file_handler)
log.addHandler(stream_handler)
log.propagate = False


# --- Configuration Class ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = BASE_DIR / "templates"


class Config:
    """
    Centralized configuration for the AutoClose Flask app.
    Keeps environment variables and project-wide constants in one place.
    """

    load_dotenv()
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    UPLOAD_FOLDER = "uploads"
    OUTPUT_ROOT = "output"
    CLIENT_REPORTS_FOLDER = os.path.join(PROJECT_ROOT, "static", "client_reports")
    ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".xlsx"}


# --- Flask App Initialization ---
app = Flask(
    __name__,
    template_folder=os.path.join(os.getcwd(), "templates"),
    static_folder=os.path.join(os.getcwd(), "static")
)
app.secret_key = "super_secret"  # כבר קיים אצלך
app.config.from_object(Config)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

# Make sure folders exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["CLIENT_REPORTS_FOLDER"], exist_ok=True)

log.info(f"🔐 Flask Secret Key: {app.config['SECRET_KEY']}")
log.info("📂 UPLOAD_FOLDER: %s", app.config["UPLOAD_FOLDER"])
log.info("📂 CLIENT_REPORTS_FOLDER: %s", app.config["CLIENT_REPORTS_FOLDER"])

# Register Blueprints
app.register_blueprint(reports_bp)
app.register_blueprint(download_bp, url_prefix="/download")
app.register_blueprint(upload_bp, url_prefix="/upload")
app.register_blueprint(search_bp)
app.register_blueprint(history_bp)
app.register_blueprint(api_reports_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_insights_bp)
app.register_blueprint(api_tasks_bp)
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api")

log.info("📍 Registered endpoints:")
log.info(app.url_map)


# --- Helper Functions ---
def allowed_file(filename: str) -> bool:
    """
    Checks if filename has an allowed extension (e.g., .txt, .pdf, .xlsx).
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        ext.lstrip(".") for ext in app.config["ALLOWED_EXTENSIONS"]
    }


def make_timestamped_filename(prefix: str, extension: str) -> str:
    """
    Creates a filename with a current timestamp:
    prefix_YYYYmmddTHHMMSS.extension
    """
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{prefix}_{ts}{extension}"


def create_reports(
    excel_path: str,
    start_date: Optional[date],
    end_date: Optional[date],
    generate_personal: bool,
    generate_monthly: bool,
) -> Tuple[list[str], Optional[str], Optional[str]]:
    """
    Loads Excel, analyzes financials, and generates reports (PDFs + Excel).
    Returns list of generated files, CSV path, and CSV filename.
    """

    # 1. Run financial analysis on uploaded file
    # Convert date to datetime if needed
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    detail_df, summary_dict = report_analyzer.build_report_data(
        excel_path, date_from=start_date, date_to=end_date
    )
    records = detail_df.to_dict(orient="records")

    # --- Generate daily income chart ---
    daily_df = summary_dict.get("daily")
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    if daily_df is not None and not daily_df.empty:
        chart_path = f"output/charts/income_chart_{ts}.png"
        save_income_chart(daily_df, Path(chart_path))
        chart_path_for_pdf: Optional[str] = chart_path
    else:
        chart_path_for_pdf = None

    generated_files: list[str] = []
    csv_path: Optional[str] = None
    csv_filename: Optional[str] = None

    # 2. Generate personal PDFs for each job
    if generate_personal:
        for record in records:
            job_id = str(record.get("job_id", "unknown"))
            name = (
                str(record.get("tech", "user")).split("/")[0].strip().replace(" ", "_")
            )
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            pdf_filename = secure_filename(f"{job_id}_{name}_{timestamp}.pdf")
            output_path = os.path.join("output/client_reports", pdf_filename)
            try:
                generate_client_pdf(record, output_path)
                generated_files.append(pdf_filename)
            except Exception as e:
                log.error(f"❌ Error generating personal PDF: {e}")

    # 3. Generate Excel summary with multiple sheets
    if generate_monthly:
        excel_name = f"monthly_summary_{start_date}_{end_date}.xlsx"
        output_path = os.path.join("output/reports_exported", excel_name)

        try:
            issues_df = run_sanity_checks(detail_df)
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                detail_df.to_excel(writer, sheet_name="Jobs", index=False)
                for name, df in summary_dict.items():
                    df.to_excel(writer, sheet_name=name[:31], index=False)
                if not issues_df.empty:
                    issues_df.to_excel(writer, sheet_name="RedFlags", index=False)
            csv_path = output_path
            csv_filename = excel_name
            generated_files.append(excel_name)
        except Exception as e:
            log.error(f"❌ Failed to generate Excel report: {e}")

        # --- RedFlag alert email to manager ---
        if not issues_df.empty:
            ts = datetime.now().strftime("%Y%m%dT%H%M%S")
            alert_path = f"output/red_flags_{ts}.xlsx"
            issues_df.to_excel(alert_path, index=False)

            emailer = EmailService(default_recipient="admin@yourdomain.com")
            emailer.send_monthly_report(
                to="admin@yourdomain.com",
                subject="Monthly Report",
                body="Attached is your monthly report.",
                pdf_path=Path(alert_path),
                start_date=str(start_date),
                end_date=str(end_date),
            )

    # --- Generate main PDF report with chart ---
    # (Assuming you want to generate a main PDF for the monthly summary)
    if generate_monthly:
        pdf_name = f"monthly_summary_{start_date}_{end_date}.pdf"
        pdf_output_path = os.path.join("output/reports_exported", pdf_name)
        try:
            generate_pdf_report(
                df=detail_df,
                output_path=pdf_output_path,
                report_type="jobs_detailed",
                title=pdf_name,
                chart_path=chart_path_for_pdf,
            )
            generated_files.append(pdf_name)
        except Exception as e:
            log.error(f"❌ Failed to generate PDF report: {e}")

    return generated_files, csv_path, csv_filename


# --- Routes ---
@app.route("/")
def index() -> Response:
    """
    Renders the main page, listing recent files in CLIENT_REPORTS_FOLDER
    and showing available report ranges from data_loader.
    """
    REPORTS_FOLDER = app.config["CLIENT_REPORTS_FOLDER"]
    MAX_DAYS = 3
    new_threshold = datetime.now() - timedelta(days=MAX_DAYS)
    file_list = []

    # Gather recently modified files
    try:
        with os.scandir(REPORTS_FOLDER) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                mtime_dt = datetime.fromtimestamp(entry.stat().st_mtime)
                is_new = mtime_dt > new_threshold
                entry_path = os.path.join(REPORTS_FOLDER, entry.name)
                exists = os.path.isfile(entry_path) and os.path.getsize(entry_path) > 0
                file_list.append(
                    {
                        "name": entry.name,
                        "is_new": is_new,
                        "modified": mtime_dt.strftime("%Y-%m-%d %H:%M"),
                        "exists": exists,
                    }
                )
        file_list.sort(
            key=lambda x: parse_date_flex(x["modified"]),
            reverse=True,
        )
    except (OSError, FileNotFoundError):
        file_list = []

    available_ranges = get_available_report_ranges()
    return cast(
        Response,
        make_response(
            render_template(
                "index.html",
                now=datetime.now(),
                file_list=file_list,
                available_ranges=available_ranges,
                current_year=datetime.now().year,
            ),
            200,
        ),
    )


def upload() -> Response:
    """
    Handles file upload or free-text input to generate detailed and summary reports,
    exports to Excel and optionally triggers the dashboard.
    """
    # Redirect GET requests to home
    if request.method == "GET":
        return cast(Response, redirect(url_for("index")))

    app.logger.info("Upload endpoint triggered.")

    # Initialize variables
    file = request.files.get("file")
    free_text = (request.form.get("free_text") or "").strip()
    range_val = request.form.get("range_selector", "")
    clean_path: Optional[str] = None
    detail_df: Optional[pd.DataFrame] = None
    summary_dict: dict[str, Any] = {}
    records: list[dict[str, Any]] = []

    # Parse date range inputs
    if "|" in range_val:
        start_input, end_input = range_val.split("|", 1)
    else:
        start_input = request.form.get("start_date", "")
        end_input = request.form.get("end_date", "")

    try:
        start_date = parse_date(start_input) if start_input else None
        end_date = parse_date(end_input) if end_input else None
    except ValueError as ve:
        app.logger.warning(f"Invalid date format: {ve}")
        return cast(
            Response,
            make_response(
                render_template("errors/error_invalid_format.html", message=str(ve)),
                400,
            ),
        )

    # Determine requested report types
    report_types = set(request.form.getlist("report_type"))
    generate_personal = "personal" in report_types
    generate_monthly = "monthly" in report_types

    # Excel file processing
    if (
        file
        and file.filename
        and app.config.get("ALLOWED_EXTENSIONS")
        and file.filename.rsplit(".", 1)[-1].lower() in app.config["ALLOWED_EXTENSIONS"]
    ):
        filename_raw = file.filename
        if filename_raw is None:
            raise ValueError("Missing filename")
        filename: str = Path(filename_raw).name
        upload_dir = Path(app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploaded_path = upload_dir / filename
        file.save(str(uploaded_path))
        app.logger.info(f"Saved uploaded file to {uploaded_path}")

        converter = XlsConverter()
        try:
            clean_path = converter.convert_to_xlsx(str(uploaded_path))
            app.logger.info(f"Converted to XLSX: {clean_path}")
        except Exception as conv_err:
            app.logger.exception("XLS conversion failed.")
            return handle_exception_context(
                context_msg="Error converting Excel file.",
                log_msg=str(conv_err),
                template_name="errors/error_processing_failed.html",
            )

        # Read the converted Excel
        try:
            detail_df = pd.read_excel(clean_path, engine="openpyxl")
            if detail_df.empty:
                flash("The Excel file contains no data.", "warning")
                return cast(Response, redirect(url_for("index")))
        except Exception as read_err:
            app.logger.exception("Failed to read XLSX file.")
            flash(
                "Failed to load the Excel file. Ensure it is a valid format.", "danger"
            )
            return cast(Response, redirect(url_for("index")))

        # Analyze report data
        try:
            detail_df, summary_dict = build_report_data(
                clean_path, date_from=start_date, date_to=end_date
            )
            records = detail_df.to_dict(orient="records")
            app.logger.info(f"Report data prepared, {len(records)} records.")
        except Exception as proc_err:
            app.logger.error(f"Data processing error: {proc_err}")
            return cast(
                Response,
                render_template(
                    "errors/error_processing_failed.html",
                    message="An error occurred during report analysis.",
                ),
            )

    # Free-text processing
    elif free_text:
        try:
            records = parse_free_text_block(free_text)
            if start_date and end_date:
                records = filter_records_by_date(records, start_date, end_date)
            if not records:
                raise ValueError("No records found in given date range.")
        except Exception as txt_err:
            app.logger.error(f"Free-text parsing failed: {txt_err}")
            return cast(
                Response,
                render_template(
                    "errors/error_processing_failed.html", message=str(txt_err)
                ),
            )
    else:
        flash("Please upload an Excel file or enter free-text records.", "info")
        return cast(Response, redirect(url_for("index")))

    # Generate PDF/CSV reports if Excel path exists
    generated_files: list[str] = []
    csv_path = None
    csv_filename = None
    if clean_path:
        generated_files, csv_path, csv_filename = create_reports(
            clean_path, start_date, end_date, generate_personal, generate_monthly
        )
        app.logger.info(f"Generated files: {generated_files}")

    # Export consolidated Excel summary
    if detail_df is not None and summary_dict:
        try:
            output_dir = Path(app.config.get("EXCEL_OUTPUT_FOLDER", "output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_report = output_dir / f"report_{timestamp}.xlsx"
            with pd.ExcelWriter(str(excel_report), engine="openpyxl") as writer:
                detail_df.to_excel(writer, sheet_name="Details", index=False)
                for sheet, df in summary_dict.items():
                    sheet_name = str(sheet)[:31]
                    if isinstance(df, pd.DataFrame):
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        pd.DataFrame([df]).to_excel(
                            writer, sheet_name=sheet_name, index=False
                        )
            app.logger.info(f"Excel summary saved: {excel_report}")
        except Exception as sum_err:
            app.logger.error(f"Summary Excel export failed: {sum_err}")

    # Route to appropriate next step
    # Priority: detailed PDF, then CSV/dashboard, else back to home
    pdf_file = next(
        (f for f in generated_files if f.startswith("Detailed_Report_")), None
    )
    if pdf_file:
        app.logger.info(f"Redirecting to PDF download: {pdf_file}")
        return cast(
            Response,
            redirect(url_for("success_page", pdf_url=f"/download-report/{pdf_file}")),
        )

    if csv_path and Path(csv_path).exists():
        os.environ["CSV_PATH"] = csv_path
        app.logger.info("CSV path set, initializing dashboard.")
        try:
            dash_app = create_dashboard(app)
            register_callbacks(dash_app)
        except Exception as dash_err:
            app.logger.error(f"Dashboard initialization failed: {dash_err}")
            flash("Dashboard launch failed after upload.", "danger")
            return cast(Response, redirect(url_for("index")))
        return cast(Response, redirect(url_for("dashboard_redirect")))

    flash("No report was created for viewing.", "warning")
    return cast(Response, redirect(url_for("index")))


@app.route("/success")
def success_page() -> Response:
    """
    Simple success page, with optional params in query string.
    """
    pdf_url = request.args.get("pdf_url")
    user_name = request.args.get("user_name")
    return cast(
        Response,
        make_response(
            render_template(
                "success/upload_success.html", pdf_url=pdf_url, user_name=user_name
            ),
            200,
        ),
    )


@app.route("/download/<filename>")
def download_file(filename: str) -> Response:
    """
    Sends a file from the CLIENT_REPORTS_FOLDER for download.
    """
    return cast(
        Response, send_from_directory(app.config["CLIENT_REPORTS_FOLDER"], filename)
    )


@app.route("/dashboard")
def dashboard_redirect() -> Response:
    # Same logic as before; no changes here
    return cast(Response, redirect(url_for("dashboard_redirect")))


# --- Example Additional Route for New Layout ---
@app.route("/dashboard/main")
def render_main_layout() -> Response:
    """
    Example route to render the main dashboard layout (new design).
    You can create 'templates/dashboard/main_layout.html' to hold the new layout.
    """
    return cast(
        Response, make_response(render_template("dashboard/main_layout.html"), 200)
    )


@app.route("/reports")
def reports_redirect() -> Response:
    """
    מפנה את הבקשות מ-/reports ל-/reports/reports
    """
    log.info("🔄 Redirecting from /reports to /reports/reports")
    try:
        return cast(Response, redirect(url_for("reports.list_reports")))
    except Exception as e:
        log.error(f"❌ Failed to redirect: {str(e)}")
        flash("שגיאה בהפניה לדוחות. נסה שוב.", "danger")
        return cast(Response, redirect(url_for("index")))


# --- Error Handlers ---
@app.errorhandler(400)
def bad_request(e: Exception) -> Response:
    return cast(
        Response,
        make_response(render_template("errors/error_invalid_format.html"), 400),
    )


@app.errorhandler(403)
def forbidden_access(e: Exception) -> Response:
    return cast(Response, make_response(render_template("errors/error_403.html"), 403))


@app.errorhandler(404)
def page_not_found(e: Exception) -> Response:
    return cast(Response, make_response(render_template("errors/error_404.html"), 404))


@app.errorhandler(500)
def internal_error(e: Exception) -> Response:
    return cast(
        Response,
        make_response(render_template("errors/error_processing_failed.html"), 500),
    )


@app.errorhandler(429)
def ratelimit_handler(e):
    log.warning(f"שגיאת קצב ({e.description}) ממשתמש {get_remote_address()}")
    return jsonify(error="⏱️ Too many uploads. Please wait a minute and try again."), 429


# --- Main Entrypoint (for local dev only) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info(f"Starting AutoCloseApp on port {port} ...")
    app.run(debug=True, host="0.0.0.0", port=port)


@app.context_processor
def inject_now() -> dict:
    return {"now": datetime.now()}


@app.before_request
def initialize_user_session():
    if "role" not in session:
        session["role"] = "tech"
        session["tech_name"] = "john.doe"
        session["client_id"] = "client123"
        log.info("Initialized default session: role=tech, tech_name=john.doe, client_id=client123")


# --- Flask-Limiter Setup (new API) ---
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# דוגמה לשימוש ב־@limiter.limit על ראוטים (יש להחיל על ה־Blueprintים/ראוטים הרלוונטיים)
#
# @app.route('/login', methods=['POST'])
# @limiter.limit("5 per minute")
# def login():
#     ...
#
# @app.route('/upload/upload', methods=['POST'])
# @limiter.limit("10 per minute")
# def upload_report():
#     ...
#
# @app.route('/api/health', methods=['GET'])
# def health_check():
#     ...  # ללא הגבלת rate
#
# @app.route('/reports/reports', methods=['GET'])
# @limiter.limit("20 per minute")
# def generate_reports():
#     ...

init_logging()
