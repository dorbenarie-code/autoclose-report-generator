# tests/test_file_validator.py

import pandas as pd
import pytest
from myapp.utils.file_validator import validate_file, InvalidCSVError


def test_validate_file_with_valid_data() -> None:
    df = pd.DataFrame(
        [
            {"technician": "David", "job_id": "001", "date": "2025-06-01"},
            {"technician": "Sara", "job_id": "002", "date": "2025-06-02"},
        ]
    )
    required_columns = ["technician", "job_id", "date"]
    result = validate_file(df, required=required_columns)
    assert result.equals(
        df
    ), "❌ validate_file should return the same DataFrame if valid"


def test_validate_file_missing_required_column() -> None:
    df = pd.DataFrame(
        [
            {"job_id": "001", "date": "2025-06-01"},
            {"job_id": "002", "date": "2025-06-02"},
        ]
    )
    required_columns = ["technician", "job_id", "date"]

    with pytest.raises(InvalidCSVError, match="Missing required columns"):
        validate_file(df, required=required_columns)
