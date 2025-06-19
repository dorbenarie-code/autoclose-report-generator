import pytest
import pandas as pd
from datetime import datetime, timedelta
from myapp.services.report_analyzer import get_income_trend_from_df


def test_get_income_trend_basic() -> None:
    """Test basic functionality with simple data"""
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-06-10", "2025-06-10", "2025-06-11"]),
            "total": [100, 150, 250],
        }
    )

    result = get_income_trend_from_df(df)

    assert isinstance(result, list)
    assert len(result) == 2

    # Check first day
    assert result[0]["date"] == "2025-06-10"
    assert result[0]["income"] == 250.0  # 100 + 150
    assert result[0]["jobs"] == 2

    # Check second day
    assert result[1]["date"] == "2025-06-11"
    assert result[1]["income"] == 250.0
    assert result[1]["jobs"] == 1


def test_get_income_trend_empty() -> None:
    """Test behavior with empty DataFrame"""
    df = pd.DataFrame(columns=["date", "total"])
    result = get_income_trend_from_df(df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_income_trend_missing_columns() -> None:
    """Test behavior with missing required columns"""
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    result = get_income_trend_from_df(df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_income_trend_date_gaps() -> None:
    """Test handling of gaps in dates"""
    dates = [
        datetime(2025, 6, 10),
        datetime(2025, 6, 10),
        datetime(2025, 6, 12),  # Gap on 11th
    ]
    df = pd.DataFrame({"date": dates, "total": [100, 200, 300]})

    result = get_income_trend_from_df(df)
    assert len(result) == 2  # Should have entries for 10th and 12th

    # Check first day
    assert result[0]["date"] == "2025-06-10"
    assert result[0]["income"] == 300.0  # 100 + 200
    assert result[0]["jobs"] == 2

    # Check second day (with gap)
    assert result[1]["date"] == "2025-06-12"
    assert result[1]["income"] == 300.0
    assert result[1]["jobs"] == 1


def test_get_income_trend_rounding() -> None:
    """Test proper rounding of income values"""
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-06-10"] * 3),
            "total": [100.123, 200.456, 300.789],
        }
    )

    result = get_income_trend_from_df(df)
    assert len(result) == 1
    assert result[0]["income"] == 601.37  # Should round to 2 decimal places


def test_get_income_trend_large_dataset() -> None:
    """Test with a larger dataset spanning multiple days"""
    # Generate 30 days of data
    base_date = datetime(2025, 6, 1)
    dates = [base_date + timedelta(days=i) for i in range(30)]
    totals = [100 + i * 10 for i in range(30)]  # Increasing trend

    df = pd.DataFrame({"date": dates, "total": totals})

    result = get_income_trend_from_df(df)
    assert len(result) == 30

    # Check first and last days
    assert result[0]["date"] == "2025-06-01"
    assert result[0]["income"] == 100.0
    assert result[0]["jobs"] == 1

    assert result[-1]["date"] == "2025-06-30"
    assert result[-1]["income"] == 390.0
    assert result[-1]["jobs"] == 1
