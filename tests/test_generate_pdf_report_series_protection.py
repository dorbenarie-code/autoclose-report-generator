import pytest
import pandas as pd
from pathlib import Path

from myapp.services.pdf_generator import generate_pdf_report
from myapp.utils.manifest import get_total, add_report_to_manifest
from myapp.utils.report_validation import validate_report_integrity


def sample_series() -> pd.Series:
    """Return a sample pandas Series named 'total'."""
    return pd.Series([100, 200, 300], name="total")


def sample_meta() -> dict:
    """Return sample metadata for manifest operations."""
    return {
        "client_id": "client123",
        "tech_name": "David",
        "report_type": "draft"
    }


@pytest.fixture
def fake_pdf(tmp_path: Path) -> Path:
    """
    Create a temporary fake PDF file path.
    This allows testing add_report_to_manifest without filesystem dependencies.
    """
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_text("")  # create an empty file
    return pdf_path


@pytest.mark.parametrize(
    "func, args, kwargs, description",
    [
        (
            generate_pdf_report,
            (sample_series(),),
            {},
            "generate_pdf_report should reject Series input"
        ),
        (
            get_total,
            (sample_series(),),
            {},
            "get_total should reject Series input"
        ),
        (
            validate_report_integrity,
            (sample_series(),),
            {},
            "validate_report_integrity should reject Series input"
        ),
    ],
)
def test_functions_reject_series(func, args, kwargs, description):
    """
    {description}
    Ensures that passing a pandas Series instead of the expected DataFrame
    raises a TypeError.
    """
    with pytest.raises(TypeError):
        func(*args, **kwargs)


def test_add_report_to_manifest_rejects_series(fake_pdf):
    """
    add_report_to_manifest should raise TypeError if df is a pandas.Series.
    """
    with pytest.raises(TypeError):
        add_report_to_manifest(
            report_path=fake_pdf,
            df=sample_series(),
            report_type="draft",
            client_id="client123",
            tech_name="David"
        )
