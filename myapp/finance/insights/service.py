from uuid import uuid4
from datetime import datetime
from myapp.finance.insights.engine import InsightsEngine
from myapp.etl.build_report_data import build_df_for_insights  # ודא שהנתיב נכון
import logging
from typing import Any, Optional
from myapp.utils.logger_config import get_logger

log = get_logger(__name__)


def format_insight(insight: Any) -> dict:
    # Extract source_file or job_id if available
    meta = getattr(insight, "meta", {}) or {}
    source_file = getattr(insight, "source_file", None) or meta.get("source_file")
    job_id = getattr(insight, "job_id", None) or meta.get("job_id")
    # Add to meta if present
    if source_file:
        meta["source_file"] = source_file
    if job_id:
        meta["job_id"] = job_id
    return {
        "id": str(uuid4()),
        "title": getattr(insight, "title", getattr(insight, "code", "Insight")),
        "message": insight.message,
        "severity": (
            "critical"
            if getattr(insight, "severity", "").lower() == "critical"
            else "info"
        ),
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "meta": meta,
    }


def get_latest_insights(limit: int = 5) -> list[dict]:
    df = build_df_for_insights()
    engine = InsightsEngine()
    try:
        insights = engine.generate(df)
    except Exception as e:
        log.exception("Failed to generate insights")
        return []
    return [format_insight(ins) for ins in insights[:limit]]
