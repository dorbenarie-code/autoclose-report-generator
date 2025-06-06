import os
import pytest
from utils import report_utils
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# === נתונים מזויפים לבדיקה ===
DUMMY_JOBS = [
    {
        "job_id": "001",
        "date": "2025-06-01",
        "technician": "David",
        "name": "Client X",
        "phone_code": "054",
        "address": "Tel Aviv",
        "job_type": "install",
        "car_info": "Mazda",
        "notes": "Urgent",
        "amount": 1200,
        "parts": 300,
        "payment_method": "Cash",
    }
]

DUMMY_TECH_DATA = [
    {"tech": "David"},
    {"tech": "David"},
    {"tech": "Eden"},
    {"tech": "Eden"},
    {"tech": "Eden"},
    {"tech": "Sara"},
]


@pytest.fixture
def valid_signature_path() -> str:
    tech_name = "San_Jose_Sapir"
    filename = tech_name.replace(" ", "_") + ".png"
    path = os.path.join("static", "signatures", filename)
    return path


def test_signature_exists_and_is_png(valid_signature_path: str) -> None:
    assert os.path.exists(
        valid_signature_path
    ), f"❌ Missing signature file: {valid_signature_path}"
    assert valid_signature_path.lower().endswith(
        ".png"
    ), "❌ Signature file is not in PNG format"


def test_create_pie_chart_base64() -> None:
    output = report_utils.create_pie_chart(DUMMY_TECH_DATA)
    assert output.startswith(
        "data:image/png;base64,"
    ), "❌ Pie chart output should start with base64 PNG header"
    assert len(output) > 1000, "❌ Pie chart base64 output too short, likely invalid"


def test_create_technician_bar_chart_base64() -> None:
    output = report_utils.create_technician_bar_chart(DUMMY_TECH_DATA)
    assert output.startswith(
        "data:image/png;base64,"
    ), "❌ Technician chart output should start with base64 PNG header"
    assert (
        len(output) > 1000
    ), "❌ Technician chart base64 output too short, likely invalid"


def test_generate_pdf_report_creates_file(tmp_path: Path) -> None:
    output_dir = tmp_path
    file_path, _ = report_utils.generate_pdf_report(
        DUMMY_JOBS, output_dir=str(output_dir)
    )
    assert os.path.exists(file_path), f"❌ PDF report was not created at {file_path}"
    assert file_path.endswith(".pdf"), "❌ Generated file is not a PDF"


def test_generate_pdf_report_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="No jobs provided for PDF generation."):
        report_utils.generate_pdf_report([])


def test_generate_client_pdf_creates_valid_pdf(tmp_path: Path) -> None:
    report_data: Dict[str, Any] = {
        "customer_name": "Test User",
        "phone": "0501234567",
        "address": "Test Address",
        "date": datetime.today().strftime("%Y-%m-%d"),
        "job_id": "A001",
        "tech": "San_Jose_Sapir",
        "company_name": "AutoClose Inc.",
        "job_type": "repair",
        "vehicle": "Toyota",
        "key_note": "Handled with care",
        "closed": "Yes",
        "total": 800,
        "cash": 400,
        "credit": 400,
        "parts": 200,
        "tech_profit": 500,
        "tech_share": "60%",
        "billing": "Company",
        "check": "N/A",
        "company_parts": "Yes",
        "balance_tech": "300",
    }

    output_path = tmp_path / "client_report_test.pdf"
    report_utils.generate_client_pdf(report_data, str(output_path))

    assert output_path.exists(), "❌ client_report.pdf was not created"
    # שים לב: גודל הקובץ לא אמור להיות אפס או קטן מידי
    assert (
        output_path.stat().st_size > 10000
    ), "❌ PDF size suspiciously small, might be empty"


@pytest.mark.parametrize(
    "invalid_data", [{}, {"tech": "NonExistent_Tech"}]  # ריק  # טכנאי ללא חתימה
)
def test_generate_client_pdf_handles_missing_or_invalid_signature(
    tmp_path: Path, invalid_data: dict
) -> None:
    output_path = tmp_path / "client_report_invalid_sig_test.pdf"
    try:
        report_utils.generate_client_pdf(invalid_data, str(output_path))
        assert (
            output_path.exists()
        ), "❌ PDF was not created with missing/invalid signature data"
        assert (
            output_path.stat().st_size > 5000
        ), "❌ PDF file too small, might be empty"
    except Exception as e:
        pytest.fail(
            f"Exception raised during PDF generation with invalid signature data: {e}"
        )
