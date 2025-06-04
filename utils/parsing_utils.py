# utils/parsing_utils.py

import re
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd

# Compiled pattern: splits on a newline when the next line starts with 5–7 uppercase letters or digits (Job ID).
_SPLIT_PATTERN = re.compile(r'\n(?=[A-Z0-9]{5,7}\b)')


def split_jobs_by_id(text: str) -> List[str]:
    """
    Split raw OCR text into separate job entries, using Job IDs as delimiters.

    A Job ID is defined as 5–7 consecutive uppercase letters or digits at the start of a line.

    Args:
        text (str): Raw text extracted via OCR.

    Returns:
        List[str]: A list of job blocks, each beginning with a Job ID.
                   Returns an empty list if input is empty or no valid blocks found.
    """
    if not text:
        return []

    trimmed = text.strip()
    raw_blocks = _SPLIT_PATTERN.split(trimmed)
    job_blocks = [block.strip() for block in raw_blocks if block.strip()]
    return job_blocks


def extract_job_data(block: str) -> Optional[Dict[str, Any]]:
    """
    Extract structured job data from a block of raw text.

    Args:
        block (str): A block of text representing one job.

    Returns:
        dict or None: Parsed job data, or None if the input block is empty.
    """
    if not block:
        return None

    lines = block.splitlines()
    data: Dict[str, Any] = {
        "job_id": None,
        "name": None,
        "phone_code": None,
        "address": None,
        "job_type": None,
        "car_info": None,
        "notes": None,           # Currently only first line after car_info
        "technician": None,
        "amount": None,
        "parts": 0.0,
        "payment_method": None,
        "date": None
    }

    # 1. Job ID from first line
    data["job_id"] = lines[0].strip()

    # 2. Name
    name_match = re.search(r"Name[:\s]*(.+)", block)
    if name_match:
        data["name"] = name_match.group(1).strip()

    # 3. Phone + Code
    phone_match = re.search(r"\(([^)]+#\d+)\)", block)
    if phone_match:
        data["phone_code"] = phone_match.group(1).strip()

    # 4. Address: line after phone block (e.g., "#123) <newline> Address")
    address_match = re.search(r"#\d+\)\s*\n(.+)", block)
    if address_match:
        data["address"] = address_match.group(1).strip()

    # 5. Job type: line immediately after the address line
    job_type_match = re.search(r"\n(?:.+#\d+\)\s*\n.+\n)(.+)", block)
    if job_type_match:
        data["job_type"] = job_type_match.group(1).strip()

    # 6. Car Info: look for a year and model (e.g., "2023 Honda Civic")
    car_match = re.search(r"\n(\d{4}\s+[A-Za-z\s]+)", block)
    if car_match:
        data["car_info"] = car_match.group(1).strip()

    # 7. Notes: first line following the car info
    if car_match:
        start = car_match.end()
        notes_match = re.search(r"\n(.+)", block[start:])
        if notes_match:
            data["notes"] = notes_match.group(1).strip()

    # 8. Technician: word immediately preceding a dollar amount
    tech_match = re.search(r"\b([A-Za-z]+)\b(?=\s*\$)", block)
    if tech_match:
        data["technician"] = tech_match.group(1).strip()

    # 9. Amount and Payment Method
    amount_match = re.search(r"(\d+\.?\d*)\$?\s*(cash|cc|zelle|venmo)?", block, re.IGNORECASE)
    if amount_match:
        data["amount"] = float(amount_match.group(1))
        if amount_match.group(2):
            data["payment_method"] = amount_match.group(2).lower()

    # 10. Parts cost
    parts_match = re.search(r"(\d+\.?\d*)\s*\$?\s*parts", block, re.IGNORECASE)
    if parts_match:
        data["parts"] = float(parts_match.group(1))

    # 11. Date (e.g., "June 5, 2023")
    date_match = re.search(r"([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})", block)
    if date_match:
        try:
            parsed_date = datetime.strptime(date_match.group(1), "%B %d, %Y")
            data["date"] = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return data


def parse_all_jobs(text: str) -> List[Dict[str, Any]]:
    """
    Parse the full raw text and return a list of structured job records.

    Steps:
      1. Split the raw text into individual job blocks.
      2. Extract data from each block using extract_job_data().
      3. Filter out any blocks where extraction returned None.
      4. Return a list of clean job dictionaries.

    Args:
        text (str): Raw OCR or text input.

    Returns:
        List[Dict[str, Any]]: List of structured job records.
    """
    blocks = split_jobs_by_id(text)
    jobs: List[Dict[str, Any]] = []

    for block in blocks:
        data = extract_job_data(block)
        if data:
            jobs.append(data)

    return jobs


def process_uploaded_file(file_path: str, start_date: str, end_date: str) -> list:
    """
    Detects file type (txt/xlsx), parses job records, and filters by date range.
    
    Args:
        file_path (str): Full path to the uploaded file.
        start_date (str): Start date in 'dd/mm/yyyy' format.
        end_date (str): End date in 'dd/mm/yyyy' format.

    Returns:
        list: Filtered list of job dictionaries.
    """
    ext = file_path.lower().split('.')[-1]
    records = []

    # Parse date range
    if isinstance(start_date, str):
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start = start_date

    if isinstance(end_date, str):
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end = end_date

    if ext == 'txt':
        with open(file_path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            # Example dummy parsing logic
            if "Honda" in line:
                record_date = datetime.strptime("20/05/2025", "%d/%m/%Y").date()  # mock
                if start <= record_date <= end:
                    records.append({"raw": line.strip(), "date": record_date})
    elif ext == 'xlsx':
        df = pd.read_excel(file_path)

        # Try to parse the "date" column
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Filter valid rows within date range
        filtered_df = df[
            (df['date'].dt.date >= start) &
            (df['date'].dt.date <= end)
        ]

        # Convert to list of dicts
        records = filtered_df.to_dict(orient='records')
    else:
        raise ValueError("Unsupported file type")

    return records
