#!/usr/bin/env python3
from pathlib import Path
from myapp.routes.upload_reports import process_upload

if __name__ == "__main__":
    import sys
    p = Path(sys.argv[1])
    process_upload(p) 