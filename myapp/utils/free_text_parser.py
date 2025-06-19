from myapp.utils.logger_config import get_logger
from myapp.utils.decimal_utils import safe_decimal

log = get_logger(__name__)
# utils/free_text_parser.py

import re


def parse_free_text_block(text: str) -> list[dict[str, float | str]]:
    """
    Parse a full free-text message and return a list of job records.
    Each record is a dictionary extracted from a block of text.
    """
    records = []
    blocks = re.split(r"\n(?=[A-Z0-9]{6,})", text.strip())  # Split by Job ID pattern

    for block in blocks:
        lines = block.strip().splitlines()
        record = {}

        for line in lines:
            line = line.strip()

            # Match Job ID
            if re.match(r"^[A-Z0-9]{6,}$", line):
                record["job_id"] = line

            # Match Name
            elif line.lower().startswith("name:"):
                record["name"] = line.split(":", 1)[-1].strip()

            # Match Total (with 'cash')
            elif "$" in line and "cash" in line.lower():
                match = re.search(r"(\d+\.?\d*)\s*\$?\s*cash", line.lower())
                if match:
                    record["total"] = safe_decimal(match.group(1))

        if record:
            records.append(record)

    return records
