from myapp.utils.logger_config import get_logger
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    Response,
    make_response,
)
from pathlib import Path
import yaml
import json
import shutil
from datetime import datetime
import csv
from myapp.utils.role_guard import role_required
from typing import Optional, cast

admin_bp = Blueprint("admin_bp", __name__)

DATA_DIR = Path("myapp/finance/_data")
TAX_FILE = DATA_DIR / "tax_history.yml"
COMM_FILE = DATA_DIR / "commission_rules.json"
VERSIONS_DIR = DATA_DIR / "versions"
AUDIT_LOG = DATA_DIR / "audit_log.csv"


def save_audit_backup(filename: Path, user: str = "admin") -> None:
    VERSIONS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_name = f"{filename.stem}_{ts}{filename.suffix}"
    backup_path = VERSIONS_DIR / backup_name
    shutil.copy2(filename, backup_path)

    # Log to audit file
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    with open(AUDIT_LOG, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.now().isoformat(),
                user,
                filename.name,
                backup_name,
            ]
        )


@admin_bp.route("/admin/rules", methods=["GET", "POST"])
@role_required("admin", "finance")
def edit_rules() -> Response:
    if request.method == "POST":
        try:
            tax_data = request.form["tax_history"]
            comm_data = request.form["commission_rules"]

            yaml.safe_load(tax_data)  # validate
            json.loads(comm_data)  # validate

            if TAX_FILE.exists():
                save_audit_backup(TAX_FILE)
            if COMM_FILE.exists():
                save_audit_backup(COMM_FILE)

            TAX_FILE.write_text(tax_data, encoding="utf-8")
            COMM_FILE.write_text(comm_data, encoding="utf-8")

            flash("✅ Rules updated successfully!", "success")
        except Exception as e:
            flash(f"❌ Error saving rules: {e}", "danger")
        return cast(Response, redirect(url_for("admin_bp.edit_rules")))

    tax_text = TAX_FILE.read_text(encoding="utf-8") if TAX_FILE.exists() else ""
    comm_text = COMM_FILE.read_text(encoding="utf-8") if COMM_FILE.exists() else ""

    return cast(
        Response,
        make_response(
            render_template(
                "admin/edit_rules.html", tax_data=tax_text, comm_data=comm_text
            ),
            200,
        ),
    )
