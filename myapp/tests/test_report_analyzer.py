import pandas as pd
from decimal import Decimal
from myapp.utils.decimal_utils import safe_decimal, apply_safe_decimal

def test_safe_decimal_basic():
    assert safe_decimal("₪1,234.56") == Decimal("1234.56")
    assert safe_decimal("   -99.9$ ") == Decimal("-99.90")
    assert safe_decimal("garbage") == Decimal("0.00")

def test_apply_safe_decimal_dataframe():
    df = pd.DataFrame({"total": ["1,000", "₪123.45"], "junk": [1, 2]})
    out = apply_safe_decimal(df, ["total"])
    assert out.iloc[0] == Decimal("1000.00")

def test_coerce_dates_handles_weird_formats():
    from myapp.utils.dataframe_utils import coerce_dates
    df = pd.DataFrame({
        "date": [
            "2025-06-10", 
            "2025-06-10T14:30:00Z", 
            None,
            "not a date"
        ]
    })
    out = coerce_dates(df, ["date"])
    assert pd.api.types.is_datetime64_any_dtype(out["date"])
    assert pd.isnull(out["date"].iloc[2])  # None
    assert pd.isnull(out["date"].iloc[3])  # 'not a date'
    assert out["date"].iloc[0].strftime("%Y-%m-%d") == "2025-06-10"

def test_enrich_financials_duration_min():
    from enrich_financials import enrich_financials
    df = pd.DataFrame({
        "date": ["2025-06-16 10:00", "2025-06-16 12:15"],
        "closed": ["2025-06-16 11:30", "2025-06-16 13:00"],
        "total": ["1,200.50", "850"],
        "parts": ["200", "50"],
        "share": ["0.5", "0.4"],
    })
    from myapp.utils.dataframe_utils import coerce_dates
    df = coerce_dates(df, ["date", "closed"])
    out = enrich_financials(df)
    assert list(out["duration_min"]) == [90, 45]
    assert out["total"].iloc[0] == 1200.50
