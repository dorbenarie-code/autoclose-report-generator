from flask import (
    Blueprint,
    send_file,
    current_app,
    abort,
    flash,
    redirect,
    url_for,
    render_template,
    Response,
    make_response,
    session,
)
from typing import Optional
import json
from pathlib import Path

from myapp.utils.logger_config import get_logger
from myapp.config_shortcuts import MANIFEST_PATH, EXPORT_DIR


download_bp = Blueprint("download_reports", __name__)
logger = get_logger(__name__)
# Directory where generated reports are stored
EXPORT_DIR = Path("output/reports_exported")

@download_bp.route("/download-report/<filename>")
def download_report(filename: str) -> Response:
    """
    Serve a PDF report file if exists and user has permissions.

    1. Verify file existence and non-zero size.
    2. Load manifest and confirm file entry.
    3. Check RBAC based on session.role, session.tech_name, session.client_id.
    4. Return file via send_file or appropriate error.

    Parameters
    ----------
    filename : str
        Name of the PDF file to download.

    Returns
    -------
    Response
        A Flask response initiating the download or redirect/error.
    """
    report_path = Path(current_app.root_path) / EXPORT_DIR / filename
    logger.info("📥 Download request for file: %s", report_path)

    # Step 1: File existence and size check
    if not report_path.is_file() or report_path.stat().st_size == 0:
        logger.error("⚠ File not found or empty: %s", report_path)
        try:
            flash("⚠ הקובץ שאתה מנסה להוריד אינו קיים או ריק.", "warning")
            return redirect(url_for("index"))  # type: ignore
        except RuntimeError:
            # No request context for flash/redirect: fallback to error page
            logger.warning("No Flask context: rendering error template for missing file")
            return make_response(
                render_template(
                    "errors/error_404.html",
                    message="הקובץ לא נמצא או נמחק."
                ),
                404,
            )

    # Step 2: Manifest-based authorization
    if MANIFEST_PATH.is_file():
        try:
            with MANIFEST_PATH.open('r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            logger.exception("Failed to load manifest.json: %s", e)
            return abort(500, "שגיאה בקריאת רשימת הדוחות")

        entry: Optional[dict] = next(
            (item for item in manifest if item.get('filename') == filename),
            None,
        )
        if entry:
            role = session.get('role', 'user')
            tech_name = session.get('tech_name', '')
            client_id = session.get('client_id', '')

            # Technician may only access their own reports
            if role == 'tech' and entry.get('tech_name') != tech_name:
                logger.warning(
                    "Unauthorized tech access attempt: tech_name=%s, file=%s",
                    tech_name,
                    filename,
                )
                return abort(403)

            # Client may only access their own reports
            if role == 'client' and entry.get('client_id') != client_id:
                logger.warning(
                    "Unauthorized client access attempt: client_id=%s, file=%s",
                    client_id,
                    filename,
                )
                return abort(403)

    # Step 3: Send file
    logger.info("✅ Authorized. Sending file: %s", filename)
    return send_file(report_path, as_attachment=True)
