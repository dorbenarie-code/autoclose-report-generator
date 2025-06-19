import json
from pathlib import Path
from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
SCHEMA_PATH = Path(__file__).resolve().parent / "schema_config.json"


def load_column_schema(report_type: str = "default") -> dict:
    """
    Load schema config for a specific report type.
    Returns dict with 'raw_to_canonical', 'date_columns', and optional metadata.
    """
    if not SCHEMA_PATH.exists():
        log.warning(f"Schema file missing: {SCHEMA_PATH}")
        return {}

    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"Schema JSON parse error: {e}")
        return {}

    return config.get(report_type, {})
