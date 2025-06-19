#!/usr/bin/env pytest
"""
CI Test: Verify full report pipeline generates a valid PDF from a dummy Excel input.
"""
import pytest
import pandas as pd
from pathlib import Path
from myapp.services.report_orchestrator import run_full_report_flow
from myapp.routes.upload_reports import process_upload
from myapp.services.pdf_generator import generate_pdf_report


def create_dummy_excel(path: Path) -> None:
    """
    Create an in-memory Excel file with the minimal schema required by the report pipeline.
    """
    df = pd.DataFrame(
        [
            {
                "job_id": "A123",
                "client_name": "Alice",
                "amount": 200,
                "tech": "Viktor",
                "date": "2025-06-01",
                "job_type": "Install",
                "address": "Tel Aviv",
                "payment_type": "cash",
                "parts": 35,
            }
        ]
    )
    df.to_excel(path, index=False)


def test_run_full_report_flow_generates_non_empty_pdf(tmp_path: Path) -> None:
    """
    Given a dummy Excel file, run the full report orchestrator without sending email,
    then assert that a non-empty PDF file is produced.
    """
    # Arrange: prepare temporary Excel input and output directory
    dummy_excel = tmp_path / "dummy_jobs.xlsx"
    create_dummy_excel(dummy_excel)

    # Act: invoke the report pipeline
    report_path_str = run_full_report_flow(
        excel_path=str(dummy_excel),
        report_title="test_pipeline",
        send_email=False,  # disable email in CI environment
    )
    report_path = Path(report_path_str)

    # Assert: verify file extension, existence, and non-zero file size
    assert (
        report_path.suffix == ".pdf"
    ), f"Expected '.pdf' extension, got '{report_path.suffix}'"
    assert report_path.exists(), f"PDF report not found at {report_path}"
    assert report_path.stat().st_size > 0, "Generated PDF file is empty"

    # Cleanup: remove generated report file
    try:
        report_path.unlink()
    except Exception:
        pass


def test_good_datafile_creates_pdf_and_manifest(tmp_path):
    test_file = Path("uploads/good_test_data.csv")

    assert test_file.exists(), "Missing test input file!"

    process_upload(test_file)

    # Check if output PDF created
    export_dir = Path("output/reports_exported")
    pdf_files = list(export_dir.glob("*.pdf"))
    assert pdf_files, "PDF was not created."

    # Check if manifest updated
    manifest = export_dir / "manifest.json"
    assert manifest.exists(), "Manifest file missing."
    data = manifest.read_text()
    assert "good_test_data" in data, "Manifest does not contain expected report entry."


def test_generate_pdf_report_rejects_series():
    df = pd.DataFrame({"amount": [10, 20]})
    with pytest.raises(TypeError):
        generate_pdf_report(df["amount"], report_type="fail")
