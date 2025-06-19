from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
logger = log
# myapp/utils.py
from typing import Any


def process_uploaded_file(
    file_path: str, start_date: str, end_date: str
) -> list[dict[str, Any]]:
    """
    Dummy version: returns hardcoded data to simulate parsed results.
    """
    return [
        {"date": "2024-12-01", "job": "install", "technician": "David"},
        {"date": "2024-12-03", "job": "repair", "technician": "Sara"},
    ]
