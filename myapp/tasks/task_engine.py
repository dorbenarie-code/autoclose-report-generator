from myapp.utils.logger_config import get_logger
from typing import Optional

log = get_logger(__name__)
from pathlib import Path
from datetime import datetime
import json
from uuid import uuid4
from myapp.finance.insights.engine import Insight

TASK_LOG = Path("output/tasks/action_items.json")


def create_action_item(
    insight: Insight, origin: str, source_file: Optional[str] = None
) -> dict:
    task = {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "severity": insight.severity,
        "message": insight.message,
        "code": insight.code,
        "meta": insight.meta,
        "origin": origin,
        "source_file": source_file,
        "status": "OPEN",
    }

    TASK_LOG.parent.mkdir(parents=True, exist_ok=True)
    if TASK_LOG.exists():
        existing = json.loads(TASK_LOG.read_text())
    else:
        existing = []

    existing.append(task)
    TASK_LOG.write_text(json.dumps(existing, indent=2))
    log.info(f"📝 Created Action Item: {task['message']}")

    return task


def load_all_tasks() -> list:
    if TASK_LOG.exists():
        return json.loads(TASK_LOG.read_text())
    return []


def update_task_status(task_id: str, status: str) -> bool:
    tasks = load_all_tasks()
    found = False
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = status
            found = True
            break
    if found:
        TASK_LOG.write_text(json.dumps(tasks, indent=2))
    return found
