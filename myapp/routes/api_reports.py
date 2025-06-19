from myapp.utils.logger_config import get_logger
from myapp.utils.date_utils import parse_date_flex
from myapp.utils.manifest import load_manifest_as_list

log = get_logger(__name__)
# routes/api_reports.py

from flask import Blueprint, jsonify, request
from datetime import datetime
from typing import List, Dict, Optional
from components.reports_table_component import get_reports_data
import os
from pathlib import Path
from myapp.services.report_analyzer import (
    build_report_data,
    get_kpi_summary,
    get_report_summary,
)

api_reports_bp = Blueprint("api_reports", __name__)


@api_reports_bp.route("/api/reports", methods=["GET"])
def get_reports() -> tuple:
    """
    REST endpoint that returns report metadata filtered by an optional date range.
    Query parameters:
      - start (YYYY-MM-DD): include reports whose start date is >= this value
      - end (YYYY-MM-DD): include reports whose start date is <= this value

    Example usage: /api/reports?start=2025-05-01&end=2025-05-31

    Returns:
        tuple: (JSON list of report objects, HTTP status code)
    """
    # Parse query parameters
    start_str: Optional[str] = request.args.get("start")
    end_str: Optional[str] = request.args.get("end")

    # Convert strings to date objects if provided
    try:
        start_date = parse_date_flex(start_str).date() if start_str else None
        end_date = parse_date_flex(end_str).date() if end_str else None
    except ValueError:
        # Invalid date format
        return (
            jsonify(
                {"error": "Invalid date format. Use YYYY-MM-DD for start and end."}
            ),
            400,
        )

    # Retrieve all available reports
    all_reports: List[Dict[str, str]] = get_reports_data()
    filtered_reports: List[Dict[str, str]] = []

    for report in all_reports:
        # Each report dict contains at least: "name", "date_range", "filename"
        date_range_str = report.get("date_range", "")
        try:
            # Extract the start date portion (before " – ")
            report_start_str = date_range_str.split(" – ")[0]
            report_start = parse_date_flex(report_start_str).date()
        except Exception:
            # Skip any report whose date_range is malformed
            continue

        # Check if the report's start date falls within the requested range
        if (start_date is None or report_start >= start_date) and (
            end_date is None or report_start <= end_date
        ):
            # Build the download URL
            report_copy = {
                "name": report["name"],
                "date_range": report["date_range"],
                "filename": report["filename"],
                "download_url": f"/download/{report['filename']}",
            }
            filtered_reports.append(report_copy)

    return jsonify(filtered_reports), 200


@api_reports_bp.route("/api/kpi/summary", methods=["GET"])
def kpi_summary() -> tuple:
    """
    Returns KPI summary for the latest available report.
    Optional query parameters:
        - path: path to Excel file
        - from, to: date filters (YYYY-MM-DD)
    """
    path = request.args.get("path", "").strip()
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    # Try parse dates
    try:
        date_from = parse_date_flex(from_str).date() if from_str else None
        date_to = parse_date_flex(to_str).date() if to_str else None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Resolve path (default = latest uploaded file)
    if not path:
        upload_dir = Path("uploads/")
        files = sorted(upload_dir.glob("*.xlsx"), key=os.path.getmtime, reverse=True)
        if not files:
            return jsonify({"error": "No report files found."}), 404
        path = str(files[0])

    # Try loading and analyzing
    try:
        df, _ = build_report_data(path, date_from=date_from, date_to=date_to)
        if df.empty:
            return jsonify({"warning": "No data in selected range."}), 204

        kpis = get_kpi_summary(df)
        return jsonify(kpis), 200

    except FileNotFoundError:
        log.warning("File not found: %s", path)
        return jsonify({"error": "File not found."}), 404

    except Exception as e:
        log.exception("Failed to compute KPIs: %s", str(e))
        return jsonify({"error": "Internal server error."}), 500


@api_reports_bp.route("/api/available-reports", methods=["GET"])
def get_available_reports():
    """
    Return a list of all reports extracted from manifest.json.
    If the file is missing or empty, load_manifest_as_list() should return [].
    """
    reports = load_manifest_as_list()
    return jsonify(reports)
