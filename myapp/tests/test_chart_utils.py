import pytest
import pandas as pd
from pathlib import Path
from myapp.utils.chart_utils import save_income_chart


def make_sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-06-01", "2024-06-01", "2024-06-02"]),
        "income": [100.0, 200.0, 150.0],
    })


def test_chart_file_created(tmp_path):
    df = make_sample_df()
    output_path = tmp_path / "chart.png"

    save_income_chart(df, output_path)

    assert output_path.is_file(), "Chart PNG file was not created"
    assert output_path.stat().st_size > 1000, "Chart file size too small to be valid"


def test_chart_with_missing_columns_warns(caplog, tmp_path):
    caplog.set_level("WARNING")
    df_missing = pd.DataFrame({"wrong": [1], "income": [100]})
    output_path = tmp_path / "chart_missing.png"

    with pytest.raises(ValueError) as exc:
        save_income_chart(df_missing, output_path)

    assert "Missing 'date' or 'income'" in str(exc.value)
    assert not output_path.exists()


def test_chart_with_empty_df_warns(caplog, tmp_path):
    caplog.set_level("WARNING")
    df_empty = pd.DataFrame(columns=["date", "income"])
    output_path = tmp_path / "chart_empty.png"

    save_income_chart(df_empty, output_path)

    assert not output_path.exists(), "Chart should not be created for empty DataFrame"
    assert any("no data provided for income chart" in rec.message.lower() for rec in caplog.records)
