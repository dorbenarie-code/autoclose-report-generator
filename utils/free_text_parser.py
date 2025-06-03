import re

def parse_free_text_block(text: str):
    """
    Parse a free-text message and return a list of job records.
    Each block starts with a Job ID (alphanumeric, 6+ chars), followed by lines containing:
      - Name: <client name>
      - <amount>$ <payment_method>  (cash, cc, or zelle)
      - <amount>$ parts
      - Technician name (e.g. "Viktor")
    Returns:
        List[dict]: One record per Job ID with keys:
            job_id (str),
            name (str),
            total (float),
            payment_method (str),
            parts (float),
            tech (str)
    """
    entries = []
    # Split text into blocks by a line starting with a Job ID (6+ uppercase letters/digits)
    blocks = re.split(r"\n(?=[A-Z0-9]{6,}$)", text.strip())

    # Precompile regexes
    job_id_pattern = re.compile(r"^[A-Z0-9]{6,}$")
    name_pattern = re.compile(r"^Name:\s*(.+)$", re.IGNORECASE)
    payment_patterns = {
        "cash": re.compile(r"(\d+\.?\d*)\s*\$?\s*cash", re.IGNORECASE),
        "cc":   re.compile(r"(\d+\.?\d*)\s*\$?\s*cc",   re.IGNORECASE),
        "zelle":re.compile(r"(\d+\.?\d*)\s*\$?\s*zelle",re.IGNORECASE),
    }
    parts_pattern = re.compile(r"(\d+\.?\d*)\s*\$?\s*parts?", re.IGNORECASE)
    # רשימת טכנאים להרחבה קלה
    TECHNICIANS = ["Viktor", "Sarah", "John"]
    tech_pattern = re.compile(r"\b(" + "|".join(map(re.escape, TECHNICIANS)) + r")\b", re.IGNORECASE)
    # תבנית למציאת טכנאי לפי פורמט קבוע במסמך
    pro_on_call_pattern = re.compile(r"PRO ON CALL SERVICES INC\s*([\w\s]+)", re.IGNORECASE)

    for block in blocks:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        record = {}

        for line in lines:
            # Check for Job ID
            if job_id_pattern.match(line):
                record["job_id"] = line
                continue

            # Check for Name
            name_match = name_pattern.match(line)
            if name_match:
                record["name"] = name_match.group(1).strip()
                continue

            lower_line = line.lower()

            # Check for payment methods (cash, cc, zelle)
            for method, pattern in payment_patterns.items():
                match = pattern.search(line)
                if match:
                    record["total"] = float(match.group(1))
                    record["payment_method"] = method
                    break
            if "payment_method" in record and "total" in record:
                continue

            # Check for Parts
            parts_match = parts_pattern.search(line)
            if parts_match:
                record["parts"] = float(parts_match.group(1))
                continue

            # Check for Technician (גמיש מרשימה)
            tech_match = tech_pattern.search(line)
            if tech_match:
                record["tech"] = tech_match.group(1)
                continue
            # Check for Technician לפי תבנית PRO ON CALL SERVICES INC <Name>
            pro_on_call_match = pro_on_call_pattern.search(line)
            if pro_on_call_match:
                record["tech"] = pro_on_call_match.group(1).strip()
                continue

        # Fill default values
        record.setdefault("name", "Unknown")
        record.setdefault("payment_method", "Unknown")
        record.setdefault("total", 0.0)
        record.setdefault("parts", 0.0)
        record.setdefault("tech", "Unknown")

        # Only include entries that have a valid job_id
        if "job_id" in record:
            entries.append(record)

    return entries
