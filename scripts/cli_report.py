#!/usr/bin/env python3
import sys
from pathlib import Path
import logging
from myapp.routes.upload_reports import process_upload

logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python cli_report.py <path/to/file.csv>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    try:
        logger.info(f"🚀 Starting report process for: {file_path}")
        process_upload(file_path)
        print("✅ Report generated successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
