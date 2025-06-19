from myapp.utils.logger_config import get_logger
from myapp.utils.date_utils import parse_date_flex

log = get_logger(__name__)
# api_insights.py

from flask import Blueprint, request, jsonify
from datetime import datetime
from pathlib import Path
import os
from myapp.services.report_analyzer import build_report_data, get_report_summary
from myapp.finance.insights.engine import InsightsEngine
from myapp.routes.api_insights_cache import INSIGHT_CACHE
import uuid

api_insights_bp = Blueprint("api_insights_bp", __name__)


@api_insights_bp.route("/api/insights", methods=["GET"])
def get_insights() -> tuple:
    """
    Returns business insights based on anomaly detection rules.
    Optional query params:
        - path: Path to Excel file
        - from: Start date (YYYY-MM-DD)
        - to: End date (YYYY-MM-DD)
        - limit: Maximum number of insights to return
    """
    path = request.args.get("path", "").strip()
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    try:
        limit = int(request.args.get("limit", 5))
    except (TypeError, ValueError):
        limit = 5

    try:
        date_from = parse_date_flex(from_str) if from_str else None
        date_to = parse_date_flex(to_str) if to_str else None
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # Default to latest Excel file in uploads/
    if not path:
        files = sorted(
            Path("uploads").glob("*.xlsx"), key=os.path.getmtime, reverse=True
        )
        if not files:
            return jsonify([]), 200
        path = str(files[0])

    try:
        df, _ = build_report_data(path, date_from=date_from, date_to=date_to)
        engine = InsightsEngine()
        insights = engine.generate(df)

        # Format insights for API response
        result = []
        now = datetime.utcnow().isoformat()

        for insight in insights:
            result.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": insight.code.replace("_", " ").title(),
                    "message": insight.message,
                    "severity": insight.severity.lower(),
                    "createdAt": now,
                    "meta": {**(insight.meta or {}), "source_file": path},
                }
            )

        # Cache insights for task creation
        INSIGHT_CACHE.add_many(result)

        return jsonify(result[:limit]), 200
    except Exception as e:
        log.exception("❌ Failed to generate insights")
        return jsonify({"error": str(e)}), 500
