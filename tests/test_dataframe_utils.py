import pytest
import pandas as pd
import numpy as np

from myapp.utils.dataframe_utils import (
    append_totals_row,
    format_currency_columns,
    safe_cast_columns,
    validate_schema,
    enrich,
)


def test_append_totals_row_basic():
    df = pd.DataFrame([
        {"job_id": "A1", "total": 100.0, "parts": 30.0},
        {"job_id": "B2", "total": 200.0, "parts": 20.0},
    ])
    result = append_totals_row(df)
    first = result.iloc[0]
    assert first["job_id"] == "Totals:2"
    assert float(first["total"]) == pytest.approx(300.0, rel=1e-3)
    assert float(first["parts"]) == pytest.approx(50.0, rel=1e-3)
    assert len(result) == 3


def test_append_totals_row_empty_df():
    df = pd.DataFrame()
    result = append_totals_row(df)
    assert result.equals(df)


def test_append_totals_row_no_numeric():
    df = pd.DataFrame([{"job_id": "A1", "name": "x"}])
    result = append_totals_row(df)
    assert result.equals(df)


def test_format_currency_columns_success():
    df = pd.DataFrame({"price": [1234.5, None], "qty": [2, 3]})
    formatted = format_currency_columns(df, ["price"])
    assert formatted.loc[0, "price"] == "1,234.50"
    assert formatted.loc[1, "price"] == ""
    assert isinstance(formatted.loc[0, "qty"], (int, np.integer))


def test_format_currency_columns_missing_column():
    df = pd.DataFrame({"a": [1]})
    missing_col = "b"
    with pytest.raises(ValueError) as exc:
        format_currency_columns(df, [missing_col])
    msg = str(exc.value)
    assert "not found" in msg
    assert missing_col in msg


def test_safe_cast_columns_success_and_failure():
    df = pd.DataFrame({"x": [1.2, 2.4], "y": ["10", "20"]})
    casted = safe_cast_columns(df, {"y": int})
    assert casted["y"].dtype == int

    with pytest.raises(ValueError) as exc1:
        safe_cast_columns(df, {"z": float})
    assert "Column 'z' not found" in str(exc1.value)

    df_invalid = pd.DataFrame({"x": [1.2, 2.4], "y": ["abc", "20"]})
    with pytest.raises(ValueError) as exc2:
        safe_cast_columns(df_invalid, {"y": int})
    assert "Failed to cast column 'y'" in str(exc2.value)


def test_validate_schema_type_mismatch_and_callable():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": ["ok", "ok", "bad"],
    })
    validate_schema(df, {"a": int})
    validator = lambda v: v in ["ok"]
    with pytest.raises(ValueError) as exc:
        validate_schema(df, {"b": validator})
    assert "invalid values" in str(exc.value)


def test_validate_schema_missing_column():
    with pytest.raises(ValueError) as exc:
        validate_schema(pd.DataFrame({"x": [1]}), {"y": int})
    assert "Missing expected columns" in str(exc.value)


BASE = pd.DataFrame(
    {
        "job_id": ["A", "B"],
        "total": [220.00, 180],
        "parts": [20, 0],
    }
)

def test_validate_schema_pass():
    validate_schema(BASE)  # לא אמור להרים חריגה

def test_validate_schema_fail():
    with pytest.raises(ValueError):
        validate_schema(pd.DataFrame({"job_id": [1]}))

def test_enrich_profit_columns():
    enriched = enrich(BASE)
    assert "tech_profit" in enriched.columns
    assert enriched.loc[0, "tech_profit"] == 100.0  # (220-20)*0.5
    assert enriched.loc[0, "balance_tech"] == -100.0
    assert enriched.loc[1, "tech_profit"] == 90.0
    assert enriched["tech_share"].unique()[0] == "50%"

def test_enrich_custom_share():
    enriched = enrich(BASE, share="40%")
    assert enriched.loc[0, "tech_profit"] == 80.0  # (220-20)*0.4

@pytest.mark.parametrize("pos", ["top", "bottom"])
def test_append_totals_row_position(pos):
    df = append_totals_row(enrich(BASE), position=pos)
    if pos == "top":
        assert df.loc[0, "job_id"].startswith("Totals")
    else:
        assert df.loc[len(df) - 1, "job_id"].startswith("Totals")

def test_totals_values():
    df = append_totals_row(enrich(BASE))
    totals = df.iloc[0]
    assert totals["total"] == pytest.approx(400.0)
    assert totals["tech_profit"] == pytest.approx(190.0)

def test_validate_numeric_column_detects_bad_values():
    from myapp.utils.decimal_utils import validate_numeric_column
    df = pd.DataFrame({
        "price": ["1,200", "$350", "bad data", "€999", "NaN", None, 0]
    })
    bad = validate_numeric_column(df, "price", sample_size=3)
    assert isinstance(bad, list)
    assert "bad data" in bad or "€999" in bad
    assert len(bad) <= 3
