from myapp.utils.logger_config import get_logger
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    make_response,
)
from pathlib import Path
import json
from myapp.utils.role_guard import role_required
from typing import Any, cast

tasks_bp = Blueprint("tasks_bp", __name__)
TASK_FILE = Path("output/tasks/action_items.json")


def load_tasks() -> list[dict[str, Any]]:
    if TASK_FILE.exists():
        return json.loads(TASK_FILE.read_text())
    return []


def save_tasks(tasks: list[dict[str, Any]]) -> None:
    TASK_FILE.write_text(json.dumps(tasks, indent=2))


@tasks_bp.route("/admin/tasks")
@role_required("admin", "manager")
def task_list() -> Response:
    tasks = load_tasks()
    severity = request.args.get("severity")
    if severity:
        tasks = [t for t in tasks if t["severity"] == severity]
    return cast(
        Response,
        make_response(render_template("admin/task_list.html", tasks=tasks), 200),
    )


@tasks_bp.route("/admin/tasks/resolve/<task_id>")
def resolve_task(task_id: str) -> Response:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "RESOLVED"
    save_tasks(tasks)
    flash("✅ Task marked as resolved", "success")
    return cast(Response, redirect(url_for("tasks_bp.task_list")))


@tasks_bp.route("/admin/tasks/delete/<task_id>")
def delete_task(task_id: str) -> Response:
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    flash("🗑️ Task deleted", "warning")
    return cast(Response, redirect(url_for("tasks_bp.task_list")))
