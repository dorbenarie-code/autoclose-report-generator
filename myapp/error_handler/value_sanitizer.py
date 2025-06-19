from myapp.utils.logger_config import get_logger
from typing import Any

logger = get_logger(__name__)
from .base import DataSanitizationError


class ValueSanitizer:
    """
    Checks for invalid characters in specified string fields.
    Ignores missing fields gracefully.
    """

    def __init__(
        self, fields_to_check: list[str], invalid_chars: str = "@#$%^&*"
    ) -> None:
        self.fields: list[str] = fields_to_check  # רשימה של שמות עמודות לבדיקה
        self.invalid_chars: set[str] = set(invalid_chars)  # קבוצת תווים אסורים

    def check(self, df: Any) -> None:
        for field in self.fields:
            if field not in df.columns:
                continue  # אם העמודה לא קיימת ב־DataFrame, מדלגים עליה
            for value in df[field]:
                # ממירים כל ערך למחרוזת ומחפשים תווים אסורים
                if any(char in str(value) for char in self.invalid_chars):
                    raise DataSanitizationError(field, value)
