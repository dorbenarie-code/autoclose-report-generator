import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from myapp.utils.normalizers import normalize_columns
from myapp.utils.report_utils import create_and_email_report
import pytest
from myapp.routes.upload_reports import process_upload


def test_run_full_report_flow():
    """
    בדיקה מלאה של יצירת דוח PDF כולל manifest.
    """
    csv_path = Path("uploads/good_test_data.csv")
    assert csv_path.exists(), f"❌ קובץ לא קיים: {csv_path}"
    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    report_path = create_and_email_report(
        df=df,
        report_type="draft_preview",
        tech_name="דוד",
        client_id="client123"
    )

    assert Path(report_path).exists(), f"❌ הדוח לא נוצר: {report_path}"


def test_single_file_success(tmp_path, caplog):
    # העתק קובץ הבדיקה לתיקיית temp
    src = Path("uploads/good_test_data.csv")
    dst = tmp_path / "good_test_data.csv"
    dst.write_bytes(src.read_bytes())

    # הכנס תיקיית temp ל־CWD כדי שה־static/fonts וכו' יסתדרו
    caplog.set_level("INFO")
    cwd = Path.cwd()
    try:
        Path.chdir(tmp_path)
        # הרץ את התהליך
        process_upload(dst)
    finally:
        Path.chdir(cwd)

    # בדוק שיצר לפחות קובץ PDF אחד בתיקיית output/reports_exported
    out_dir = tmp_path / "output" / "reports_exported"
    files = list(out_dir.glob("*.pdf"))
    assert files, "אין PDF בתיקיית output/reports_exported"

    # ודא שה־manifest.json עודכן
    manifest = tmp_path / "output" / "reports_exported" / "manifest.json"
    assert manifest.exists(), "manifest.json לא קיים"
