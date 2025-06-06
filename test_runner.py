import sys
from pathlib import Path
import argparse
import logging
from pprint import pprint
from utils.parsing_utils import process_uploaded_file

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "myapp"))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Process a legacy Excel report and filter by date range."
    )
    parser.add_argument(
        "file_path", type=str, help="Path to the input .xls or .xlsx file."
    )
    parser.add_argument("start_date", type=str, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("end_date", type=str, help="End date in YYYY-MM-DD format.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.file_path)

    # בדיקה אם הקובץ קיים בפועל
    if not input_path.exists():
        logging.error(f"File not found: {input_path}")
        sys.exit(1)

    try:
        records = process_uploaded_file(str(input_path), args.start_date, args.end_date)
        logging.info(f"Loaded {len(records)} records.")
        pprint(records)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # הגדרת פורמט לוג בסיסי
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
