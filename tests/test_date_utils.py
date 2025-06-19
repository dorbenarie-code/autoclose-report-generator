import pytest
from datetime import datetime
from myapp.utils.date_utils import parse_date_flex

@pytest.mark.parametrize("date_str, expected", [
    ("2025-06-10", datetime(2025, 6, 10)),
    ("2025-06-10 14:30:00", datetime(2025, 6, 10, 14, 30, 0)),
    ("2025-06-10T14:30:00", datetime(2025, 6, 10, 14, 30, 0)),
    ("2025-06-10T14:30:00.123Z", datetime(2025, 6, 10, 14, 30, 0, 123000)),
    ("2025/06/10", datetime(2025, 6, 10)),
])
def test_parse_date_flex_valid_formats(date_str, expected):
    result = parse_date_flex(date_str)
    assert result == expected

def test_parse_date_flex_invalid():
    with pytest.raises(ValueError):
        parse_date_flex("10-06-2025")
    with pytest.raises(ValueError):
        parse_date_flex("not-a-date")

def test_parse_date_flex_datetime_passthrough():
    now = datetime(2025, 6, 10, 15, 0)
    assert parse_date_flex(now) == now

def test_parse_date_flex_am_pm_format():
    dt = parse_date_flex("05/20/2025 10:00 AM")
    assert dt.year == 2025
    assert dt.month == 5
    assert dt.day == 20
    assert dt.hour == 10

def test_am_pm_us_format():
    result = parse_date_flex("05/25/2025 08:30 PM")
    assert result.hour == 20
