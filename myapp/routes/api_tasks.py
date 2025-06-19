from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from flask import Blueprint, request, jsonify
from types import SimpleNamespace
from myapp.routes.api_insights_cache import INSIGHT_CACHE
from myapp.tasks.task_engine import (
    create_action_item,
    load_all_tasks,
    update_task_status,
)
from myapp.finance.insights.engine import Insight

api_tasks_bp = Blueprint("api_tasks_bp", __name__)


@api_tasks_bp.route("/api/tasks", methods=["POST"])
def create_task_from_insight() -> tuple:
    data = request.get_json(force=True, silent=True)
    if not data or "insightId" not in data:
        return jsonify({"error": "Missing required field: insightId"}), 400

    insight = INSIGHT_CACHE.get(data["insightId"])
    if not insight:
        return jsonify({"error": "Insight not found"}), 404

    insight_obj = Insight(
        code=insight["id"],
        message=insight["message"],
        severity=insight["severity"],
        meta={"title": insight["title"], "createdAt": insight["createdAt"]},
    )

    task = create_action_item(insight=insight_obj, origin="insight")
    task_id = task.get("id") if isinstance(task, dict) and "id" in task else None

    return jsonify({"status": "created", "taskId": task_id}), 200


@api_tasks_bp.route("/api/tasks", methods=["GET"])
def get_all_tasks() -> tuple:
    tasks = load_all_tasks()
    return jsonify(tasks), 200


@api_tasks_bp.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id: str) -> tuple:
    data = request.get_json(force=True, silent=True)
    if not data or "status" not in data:
        return jsonify({"error": "Missing required field: status"}), 400
    status = data["status"]
    allowed = {"Open", "Resolved"}
    if status not in allowed:
        return (
            jsonify({"error": f"Invalid status. Must be one of: {', '.join(allowed)}"}),
            400,
        )
    updated = update_task_status(task_id, status)
    if not updated:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"status": "updated", "taskId": task_id}), 200
