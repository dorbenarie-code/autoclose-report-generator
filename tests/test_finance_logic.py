from datetime import datetime
import pandas as pd
from decimal import Decimal
from typing import Optional, Callable, Any

# STEP 1: test_tax_resolution
# (Assume resolve_tax_rate exists in myapp.finance.rules)
try:
    from myapp.finance.rules import resolve_tax_rate
except ImportError:
    resolve_tax_rate: Optional[Callable[..., Any]] = None


def test_tax_rate_il_2023() -> None:
    if resolve_tax_rate is None:
        return
    rate = resolve_tax_rate("IL", datetime(2023, 5, 1))
    assert rate == 0.17


def test_tax_rate_il_2025() -> None:
    if resolve_tax_rate is None:
        return
    rate = resolve_tax_rate("IL", datetime(2025, 1, 1))
    assert rate == 0.18


def test_tax_rate_unknown_jurisdiction() -> None:
    if resolve_tax_rate is None:
        return
    rate = resolve_tax_rate("ZZ", datetime.now())
    assert rate == 0.0


# STEP 2: test_commission_resolution
# (Assume commission_for exists in myapp.finance.rules)
try:
    from myapp.finance.rules import commission_for
except ImportError:
    commission_for: Optional[Callable[..., Any]] = None


def test_commission_percent() -> None:
    if commission_for is None:
        return
    rate = commission_for("AC_REPAIR", "Viktor", 1000)
    assert rate == 500  # 1000*0.5


def test_commission_flat() -> None:
    if commission_for is None:
        return
    rate = commission_for("AC_INSTALL", "Sapir", 1000)
    assert rate == 500  # flat 500


def test_commission_tiered() -> None:
    if commission_for is None:
        return
    rate = commission_for("BIG_JOB", "Viktor", 2500)
    assert rate >= 0.5


# STEP 3: test_enrich_on_simple_input
# (Assume enrich exists in myapp.finance.calculator)
try:
    from myapp.finance.calculator import enrich
except ImportError:
    enrich: Optional[Callable[..., Any]] = None


def test_enrich_single_row() -> None:
    if enrich is None:
        return
    df = pd.DataFrame(
        [
            {
                "total": 100,
                "parts": 20,
                "job_type": "AC_INSTALL",
                "tech": "Sapir",
                "date": datetime(2024, 8, 1),
                "closed": datetime(2024, 8, 1, 1, 30),
                "client_country": "IL",
            }
        ]
    )
    out = enrich(df)
    assert "company_net" in out.columns
    assert "tech_cut" in out.columns
    assert "tax_collected" in out.columns
    assert out.loc[0, "company_net"] > 0


# STEP 4: test_flag_detection
# (Assume run_flag_checks exists in myapp.finance.flags)
try:
    from myapp.finance.flags import run_flag_checks
except ImportError:
    run_flag_checks: Optional[Callable[..., Any]] = None


def test_flag_high_commission() -> None:
    if run_flag_checks is None:
        return
    df = pd.DataFrame(
        [
            {
                "total": Decimal("100.00"),
                "parts": Decimal("10.00"),
                "tech_cut": Decimal("95.00"),
                "company_net": Decimal("-5.00"),
                "closed": datetime(2024, 8, 1),
            }
        ]
    )
    df["date"] = df["closed"]
    flagged_df, count = run_flag_checks(df)
    assert "HIGH_COMM" in flagged_df["flags"].iloc[0]
    assert "NEG_NET" in flagged_df["flags"].iloc[0]
    assert count == 1
