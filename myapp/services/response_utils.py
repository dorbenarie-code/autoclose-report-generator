# services/response_utils.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Hashable

from flask import flash, render_template, make_response, Response
from jinja2 import TemplateNotFound
import os
from pathlib import Path
from myapp.utils.logger_config import get_logger

log = get_logger(__name__)


def _build_context(
    file_list: Optional[list[dict[str, Any]]] = None,
) -> dict[Hashable, Any]:
    """
    Construct the standard template context.

    :param file_list: List of report dictionaries (each with keys like 'name', 'is_new', 'modified').
    :return: A context dict containing 'file_list' and current timestamp 'now'.
    """
    return {
        "file_list": file_list if file_list is not None else [],
        "now": datetime.now(),  # Use local time; switch to datetime.utcnow() if UTC is preferred
    }


def render_with_context(
    message: Optional[str] = None,
    category: str = "info",
    file_list: Optional[list[dict[str, Any]]] = None,
    status_code: int = 200,
    template_name: str = "index.html",
) -> Response:
    """
    Render a template with the standard context and optional flash message.

    Edge cases handled:
      - If `message` is None or empty, skip flash.
      - If `status_code` is outside valid HTTP range (100–599), fallback to 200.
      - If template is not found, log the error and return a minimal error message.

    :param message: Message to flash (display to the user). If falsy, no flash is called.
    :param category: Flash category (e.g., 'info', 'success', 'danger').
    :param file_list: List of report items to include; each should be a dict.
    :param status_code: Desired HTTP status code.
    :param template_name: Jinja template filename to render.
    :return: Tuple of (rendered HTML string or simple error string, status code).
    """
    # Validate status_code: must be between 100 and 599
    if not (100 <= status_code < 600):
        log.warning(
            "Invalid status_code %r received in render_with_context; defaulting to 200.",
            status_code,
        )
        status_code = 200

    # Only flash if there's a non-empty message
    if message:
        try:
            flash(message, category)
        except RuntimeError as e:
            log.exception("Flash failed in render_with_context: %s", e)

    context = _build_context(file_list)

    try:
        rendered = render_template(
            template_name, file_list=context["file_list"], now=context["now"]
        )
        return make_response(rendered, status_code)
    except TemplateNotFound:
        log.error("Template %r not found in render_with_context.", template_name)
        # Fallback minimal HTML to indicate the error
        fallback = (
            f"<h1>Template Not Found</h1>"
            f"<p>Unable to locate template: {template_name}</p>"
        )
        return make_response(fallback, 500)
    except Exception as e:
        log.exception("Unexpected error rendering %r: %s", template_name, e)
        # Generic error response if rendering fails for another reason
        fallback = (
            f"<h1>Rendering Error</h1>"
            f"<p>There was an error rendering the page. Please try again later.</p>"
        )
        return make_response(fallback, 500)


def handle_exception_context(
    context_msg: str,
    log_msg: str = "Unexpected error occurred",
    file_list: Optional[list[dict[str, str]]] = None,
    template_name: str = "errors/error_processing_failed.html",
) -> Response:
    """
    מטפל בשגיאה על ידי:
    - כתיבת לוג עם מחסנית שגיאה
    - הוספת Flash למשתמש (אם אפשר)
    - החזרת דף HTML רלוונטי עם קוד 500
    """
    # כתיבת שגיאה ללוג
    log.exception(log_msg)

    # נסיון לבצע flash (אם אפשר)
    try:
        flash(context_msg, "danger")
    except Exception as e:
        log.debug("⚠️ Flash failed (not in request context?): %s", e)

    # בניית קונטקסט לתבנית
    context = {"file_list": file_list or [], "now": datetime.now()}

    # נסיון לטעון תבנית מותאמת
    try:
        rendered = render_template(
            template_name, file_list=context["file_list"], now=context["now"]
        )
        return make_response(rendered, 500)
    except TemplateNotFound:
        log.error("❌ Template not found: %s", template_name)
        return make_response("<h1>Template Not Found</h1>", 500)
    except Exception as e:
        log.exception("❌ Failed to render error template: %s", e)
        return make_response("<h1>Critical Error</h1><p>Something went wrong.</p>", 500)


def get_file_list_for_render(
    folder: str = "backup/client_reports",
) -> list[dict[str, Any]]:
    """
    Returns a list of report dictionaries with metadata for the UI.
    Only includes files that exist and are not empty.
    """
    file_list = []
    threshold = datetime.now().timestamp() - (2 * 86400)
    folder_path = Path(folder)

    if not folder_path.exists():
        return []

    for f in sorted(folder_path.iterdir(), reverse=True):
        if not f.is_file() or not f.suffix.lower().endswith(".pdf"):
            continue
        if not f.exists() or f.stat().st_size == 0:
            continue  # Skip files that do not exist or are empty
        mtime = f.stat().st_mtime
        file_list.append(
            {
                "name": f.name,
                "is_new": mtime > threshold,
                "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )
    return file_list


def log_upload_triggered() -> None:
    log.info("✅ upload() triggered")


def log_upload_check() -> None:
    log.info("🚀 upload() triggered – logger check")
