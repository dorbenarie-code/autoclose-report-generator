from flask import Blueprint, request, jsonify
from datetime import datetime
import os
from pathlib import Path
import logging
from myapp.services.report_analyzer import build_report_data, get_income_trend
from myapp.utils.date_utils import parse_date_flex

# Setup logger
log = logging.getLogger(__name__)

# Create Blueprint
api_reports_bp = Blueprint("api_reports", __name__)


@api_reports_bp.route("/api/kpi/income_trend", methods=["GET"])
def income_trend_api() -> tuple:
    """
    Returns daily income trend for dashboard charts.

    Optional query parameters:
        - path: Path to Excel file (defaults to latest file in uploads/)
        - from: Start date in YYYY-MM-DD format
        - to: End date in YYYY-MM-DD format

    Returns:
        tuple: (JSON response, HTTP status code)

    Example response:
        [
            {"date": "2025-06-10", "income": 1334.22, "jobs": 5},
            {"date": "2025-06-11", "income": 1012.11, "jobs": 3}
        ]
    """
    log.info("Processing income trend API request")

    # Parse query parameters
    path = request.args.get("path", "").strip()
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    # Validate and parse dates
    try:
        date_from = parse_date_flex(from_str) if from_str else None
        date_to = parse_date_flex(to_str) if to_str else None

        if date_from and date_to and date_from > date_to:
            log.warning("Invalid date range: from=%s, to=%s", from_str, to_str)
            return jsonify({"error": "Start date must be before end date"}), 400

    except ValueError as e:
        log.warning("Invalid date format: %s", str(e))
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Resolve file path
    if not path:
        log.info("No path provided, using latest file from uploads/")
        files = sorted(
            Path("uploads/").glob("*.xlsx"), key=os.path.getmtime, reverse=True
        )
        if not files:
            log.warning("No Excel files found in uploads/")
            return jsonify([]), 200
        path = str(files[0])
        log.info("Using latest file: %s", path)

    try:
        # Load and process data
        df, _ = build_report_data(path, date_from=date_from, date_to=date_to)
        if df.empty:
            log.warning("No data found in selected date range")
            return jsonify([]), 200

        # Compute trend
        trend_data = get_income_trend(df)
        log.info("Successfully computed trend with %d records", len(trend_data))
        return jsonify(trend_data), 200

    except FileNotFoundError:
        log.error("File not found: %s", path)
        return jsonify({"error": "File not found"}), 404

    except Exception as e:
        log.exception("Failed to compute income trend: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500
