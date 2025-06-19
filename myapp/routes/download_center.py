from flask import Blueprint, jsonify, session
import json
from pathlib import Path
from myapp.config_shortcuts import MANIFEST_PATH

download_bp = Blueprint("download_center", __name__, url_prefix="/reports")

@download_bp.route("/download-center", methods=["GET"])
def get_available_reports():
    if not MANIFEST_PATH.is_file():
        return jsonify([])

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    role = session.get("role", "user")
    tech_name = session.get("tech_name", "")
    client_id = session.get("client_id", "")

    if role == "tech":
        manifest = [r for r in manifest if r.get("tech_name") == tech_name]
    elif role == "client":
        manifest = [r for r in manifest if r.get("client_id") == client_id]

    return jsonify(manifest)
