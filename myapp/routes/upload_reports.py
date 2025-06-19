from myapp.utils.date_utils import parse_date_flex
# routes/upload_reports.py

from flask import (
    Blueprint,
    request,
    jsonify,
    url_for,
    current_app,
    Response,
    make_response,
    session,
    redirect,
    flash,
)
from pathlib import Path
import logging
import os
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from typing import Optional
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
import shutil

from myapp.error_handler.xls_converter import XlsConverter
from myapp.error_handler.base import FileFormatError

from myapp.utils.file_uploader import save_uploaded_file
from myapp.utils.parsing_utils import load_and_validate_excel
from myapp.services.mail_utils import send_report_by_email
from myapp.utils.file_validator import (
    validate_file_extension,
    validate_file_size,
    validate_file_count,
    validate_email,
    MAX_FILES_PER_UPLOAD,
)
from myapp.utils.report_utils import create_and_email_report
from myapp.utils.manifest import load_manifest_as_list
from myapp.utils.logger_config import get_logger

upload_bp = Blueprint("upload_reports", __name__)

UPLOAD_FOLDER = Path("uploads/")
OUTPUT_CSV = Path("output/merged_jobs.csv")

log = get_logger(__name__)

# Rate limit per tech_name (falls back to IP)
limiter = Limiter(key_func=lambda: session.get("tech_name") or get_remote_address())

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@upload_bp.route("/upload", methods=["POST"])
@limiter.limit("10 per minute", override_defaults=False)
def upload_report() -> Response:
    """
    מטפל בהעלאת קבצים ושליחת דוחות.
    מחזיר תשובה בפורמט JSON עם סטטוס והודעות שגיאה.
    """
    log.debug("TYPECHECK: about to process upload_report")
    try:
        # בדיקת אימייל
        recipient_email = request.form.get("recipient_email")
        if not recipient_email:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "נא להזין כתובת אימייל",
                        "field": "recipient_email",
                    }
                ),
                400,
            )

        if not validate_email(recipient_email):
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "כתובת האימייל אינה תקינה",
                        "field": "recipient_email",
                    }
                ),
                400,
            )

        # בדיקת תאריכים
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not start_date_str or not end_date_str:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "נא להזין תאריך התחלה ותאריך סיום",
                        "field": "date_range",
                    }
                ),
                400,
            )

        try:
            start_date = parse_date_flex(start_date_str)
            end_date = parse_date_flex(end_date_str)

            if end_date < start_date:
                return make_response(
                    jsonify(
                        {
                            "status": "error",
                            "message": "תאריך הסיום חייב להיות אחרי תאריך ההתחלה",
                            "field": "date_range",
                        }
                    ),
                    400,
                )

        except ValueError:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "פורמט תאריך לא תקין. נא להשתמש בפורמט YYYY-MM-DD",
                        "field": "date_range",
                    }
                ),
                400,
            )

        # בדיקת קבצים
        if "excel_files" not in request.files:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "לא נבחרו קבצים",
                        "field": "excel_files",
                    }
                ),
                400,
            )

        excel_files = request.files.getlist("excel_files")

        if not excel_files or all(f.filename == "" for f in excel_files):
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "לא נבחרו קבצים",
                        "field": "excel_files",
                    }
                ),
                400,
            )

        if not validate_file_count(excel_files):
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": f"יותר מדי קבצים. מקסימום {MAX_FILES_PER_UPLOAD} קבצים מותרים",
                        "field": "excel_files",
                    }
                ),
                400,
            )

        results = []

        for file in excel_files:
            if not file or not file.filename:
                continue

            filename = secure_filename(file.filename)
            filepath = str(UPLOAD_FOLDER / filename)
            file.save(filepath)
            log.info(f"[UPLOAD] File saved: {filepath}")

            # validate size
            if not validate_file_size(filepath):
                results.append(
                    {"filename": filename, "status": "error", "message": "הקובץ גדול מדי", "field": "excel_files"}
                )
                log.debug(f"[UPLOAD] partial result: {results[-1]}")
                os.remove(filepath)
                continue

            try:
                # load DataFrame
                df = pd.read_csv(filepath) if filename.lower().endswith(".csv") else pd.read_excel(filepath, engine="openpyxl")
                log.debug("TYPECHECK: %s in upload_report (df loaded from file)", type(df).__name__)

                # prepare params
                r_type = Path(filename).stem
                c_id = session.get("client_id", "default_client")

                # save UX info to session
                session["last_uploaded_filename"] = filename

                # TODO: wrap this call in a background thread or Celery task in the future
                report_path = create_and_email_report(
                    df=df, report_type=r_type, tech_name=session.get("tech_name", "אנונימי"), client_id=c_id
                )

                # save report path to session
                session["last_report_path"] = str(report_path) if report_path else ""

                if report_path:
                    download_url = url_for("download_reports.download_report", filename=os.path.basename(report_path), _external=True)

                    # fetch metadata for smart summary
                    manifest = load_manifest_as_list()
                    meta = next((r for r in manifest if r.get("filename") == os.path.basename(report_path)), {})

                    results.append(
                        {
                            "filename": filename,
                            "status": "success",
                            "download_url": download_url,
                            "created_at": meta.get("created_at", ""),
                            "total": meta.get("total", 0),
                            "rows": meta.get("rows", 0),
                            "report_type": r_type,
                            "client_id": c_id,
                            "message": "הדוח נוצר ונשלח בהצלחה",
                        }
                    )
                else:
                    results.append(
                        {
                            "filename": filename,
                            "status": "error",
                            "message": "יצירת הדוח או שליחת המייל נכשלו. בדוק את הלוגים",
                            "field": "report_generation",
                            "report_type": r_type,
                            "client_id": c_id,
                        }
                    )

                log.debug(f"[UPLOAD] partial result: {results[-1]}")

            except Exception as e:
                log.error(f"[UPLOAD] Error processing {filename}: {e}", exc_info=True)
                results.append(
                    {
                        "filename": filename,
                        "status": "error",
                        "message": f"שגיאה בעיבוד הקובץ: {e}",
                        "field": "file_processing",
                        "report_type": r_type if 'r_type' in locals() else Path(filename).stem,
                        "client_id": c_id if 'c_id' in locals() else session.get("client_id", "default_client"),
                    }
                )
                log.debug(f"[UPLOAD] partial result: {results[-1]}")

            finally:
                # Backup before deletion
                debug_dir = UPLOAD_FOLDER / "debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                backup_path = debug_dir / filename
                try:
                    shutil.copy(filepath, backup_path)
                    log.info(f"[UPLOAD] File backed up to: {backup_path}")
                except Exception as backup_err:
                    log.warning(f"[UPLOAD] Could not backup file: {backup_err}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    log.info(f"[UPLOAD] Temp file removed: {filepath}")

        # Post-processing results
        results = [{k: v or "" for k, v in r.items()} for r in results]

        # If no success at all – clearer error message
        if not any(r["status"] == "success" for r in results):
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": "לא הצלחנו לעבד אף קובץ. בדוק אם יש עמודות חסרות, שגיאות בתאריכים או פורמט לא נתמך",
                        "results": results,
                    }
                ),
                400,
            )

        # Summary for UX
        total_reports = sum(1 for r in results if r["status"] == "success")
        total_sum = sum(r.get("total", 0) for r in results if r["status"] == "success")
        tech = session.get("tech_name", "")

        return make_response(
            jsonify(
                {
                    "status": "success",
                    "message": "הקבצים עובדו בהצלחה",
                    "results": results,
                    "summary": {"total_reports": total_reports, "total_sum": total_sum, "tech": tech},
                }
            ),
            200,
        )

    except Exception as e:
        log.error(f"[UPLOAD] General error: {e}", exc_info=True)
        return make_response(jsonify({"status": "error", "message": "שגיאה כללית בעיבוד הבקשה", "error": str(e)}), 500)

def process_upload(file_path: Path) -> str:
    logger = logging.getLogger(__name__)
    logger.debug("TYPECHECK: %s in process_upload", type(file_path).__name__)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        logger.info(f"[PROCESS_UPLOAD] Reading file: {file_path}")
        df = pd.read_csv(file_path) if file_path.suffix.lower() == ".csv" else pd.read_excel(file_path, engine="openpyxl")
        logger.debug("TYPECHECK: %s in process_upload (df loaded from file)", type(df).__name__)
        logger.info(f"[PROCESS_UPLOAD] Loaded DataFrame with shape {df.shape}")
        # You can add more context/params as needed
        report_path = create_and_email_report(
            df=df,
            report_type=file_path.stem,
            tech_name=df["technician"].iloc[0] if "technician" in df.columns else "",
            client_id=df["company"].iloc[0] if "company" in df.columns else ""
        )
        logger.info(f"[PROCESS_UPLOAD] Report generated: {report_path}")
        return report_path
    except Exception as e:
        logger.exception(f"[PROCESS_UPLOAD] Failed to process {file_path}: {e}")
        raise
