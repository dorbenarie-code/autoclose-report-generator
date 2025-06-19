from myapp.utils.logger_config import get_logger
from myapp.utils.date_utils import parse_date_flex
from myapp.utils.decimal_utils import safe_decimal

log = get_logger(__name__)
from datetime import datetime
from typing import Optional, Union, Any


def format_currency(value: Any) -> str:
    """
    ממיר ערך למחרוזת כספית בפורמט ₪X.XX
    """
    try:
        return f"₪{safe_decimal(value):,.2f}"
    except (ValueError, TypeError):
        return "₪0.00"


def format_date(dt: Optional[str | datetime]) -> str:
    """
    ממיר תאריך לפורמט DD/MM/YYYY או מחזיר ריק אם לא תקין
    """
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt_obj = parse_date_flex(dt)
            return dt_obj.strftime("%d/%m/%Y")
        except Exception:
            return dt  # fallback: return as-is if not parseable
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return str(dt)
