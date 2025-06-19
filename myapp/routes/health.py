from flask_smorest import Blueprint
from flask import jsonify
from marshmallow import Schema, fields
from pathlib import Path

health_bp = Blueprint('health', __name__, url_prefix='/api')

class HealthResponseSchema(Schema):
    status = fields.Str(required=True)
    build = fields.Str(required=True)
    git = fields.Str(required=True)

def get_version() -> str:
    version_file = Path("VERSION")
    return version_file.read_text().strip() if version_file.exists() else "unknown"

def get_git_hash() -> str:
    try:
        import subprocess
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"

@health_bp.route('/health', methods=['GET'])
@health_bp.response(200, HealthResponseSchema)
def health_check():
    """בדיקת מצב השרת"""
    return {
        "status": "ok",
        "build": get_version(),
        "git": get_git_hash(),
    }