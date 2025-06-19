import json
import logging
from pathlib import Path
import pandas as pd
import pytest

from myapp.utils.report_validation import validate_report_integrity


def test_pdf_not_found(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    missing_pdf = tmp_path / "nonexistent.pdf"
    df = pd.DataFrame({"job_id": ["A1"], "total": [100.0]})

    with pytest.raises(ValueError) as exc:
        validate_report_integrity(missing_pdf, df)

    assert "PDF report not found" in str(exc.value)
    assert any(
        "PDF report not found" in record.message and record.levelname == "ERROR"
        for record in caplog.records
    )


def test_pdf_too_small(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    small_pdf = tmp_path / "small.pdf"
    # Write a file smaller than threshold (10 KB)
    small_pdf.write_bytes(b"a" * 5000)
    df = pd.DataFrame({"job_id": ["A1"], "total": [100.0]})

    with pytest.raises(ValueError) as exc:
        validate_report_integrity(small_pdf, df)

    assert "Generated PDF seems incomplete or corrupt." in str(exc.value)
    assert any(
        "Generated PDF is too small" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    )


def test_insufficient_rows(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    valid_pdf = tmp_path / "valid.pdf"
    # Write a valid-size PDF placeholder
    valid_pdf.write_bytes(b"b" * 20000)
    # DataFrame with only a totals row
    df = pd.DataFrame([{"job_id": "Totals:1", "total": 100.0}])

    with pytest.raises(ValueError) as exc:
        validate_report_integrity(valid_pdf, df, totals_label="Totals:")

    assert "Report contains no meaningful data." in str(exc.value)
    assert any(
        "insufficient data rows" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    )


def test_non_positive_total(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    valid_pdf = tmp_path / "valid2.pdf"
    valid_pdf.write_bytes(b"c" * 20000)
    # DataFrame with non-positive total sum
    df = pd.DataFrame([
        {"job_id": "A1", "total": -50.0},
        {"job_id": "B2", "total": 0.0},
    ])

    with pytest.raises(ValueError) as exc:
        validate_report_integrity(valid_pdf, df)

    assert "Report total is zero or negative." in str(exc.value)
    assert any(
        "Report total sum is non-positive" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    )
