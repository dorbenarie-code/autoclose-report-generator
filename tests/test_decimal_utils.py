import pandas as pd
from decimal import Decimal
from myapp.utils.decimal_utils import safe_decimal, apply_safe_decimal, validate_numeric_column

def test_safe_decimal_basic():
    assert safe_decimal("₪1,234.56") == Decimal("1234.56")
    assert safe_decimal("   -99.9$ ") == Decimal("-99.90")
    assert safe_decimal("garbage") == Decimal("0.00")

def test_apply_safe_decimal_dataframe():
    df = pd.DataFrame({"total": ["1,000", "₪123.45"], "junk": [1, 2]})
    out = apply_safe_decimal(df, ["total"])
    assert out["total"].iloc[0] == Decimal("1000.00")

def test_validate_numeric_column_detects_bad_values():
    df = pd.DataFrame({
        "price": ["1,200", "$350", "bad data", "€999", "NaN", None, 0]
    })
    bad = validate_numeric_column(df, "price", sample_size=3)
    assert isinstance(bad, list)
    assert any("bad" in x or "€" in x for x in bad)

def test_safe_decimal_valid() -> None:
    from myapp.utils.decimal_utils import safe_decimal
    assert safe_decimal("100.556") == Decimal("100.56")
    assert safe_decimal(123) == Decimal("123.00")
    assert safe_decimal(None) == Decimal("0.00")
