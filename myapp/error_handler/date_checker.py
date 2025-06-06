import logging
from typing import Optional
import pandas as pd
from .base import InvalidDateError, MissingColumnError


class DateChecker:
    """
    Validates that all values in a specified date column can be parsed as dates.
    - Skips empty or NaN values.
    - Skips strings without any digits (e.g., 'billing').
    - Optionally enforces a specific date format.

    Args:
        date_column (str): Name of the column to validate.
        date_format (Optional[str]): If provided, uses this format in
            pd.to_datetime(..., format=...).
        logger (logging.Logger | None): Logger for debug messages.
            If None, a default logger is used.
    """

    def __init__(
        self,
        date_column: str = "date",
        date_format: Optional[str] = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.date_column = date_column
        self.date_format = date_format
        self.logger = logger or logging.getLogger(__name__)

    def check(self, df: pd.DataFrame) -> None:
        """
        בודק שכל ערך בעמודת התאריך ניתן להמרה לתאריך תקני.
        זורק InvalidDateError בערך הראשון שאינו תקין.

        Args:
            df (pd.DataFrame): DataFrame המכיל את עמודת התאריכים.

        Raises:
            MissingColumnError: אם העמודה אינה קיימת ב־df.
            InvalidDateError: אם נמצא ערך בתאריך שאי אפשר להמיר.
        """
        # בדיקה אם העמודה קיימת
        if self.date_column not in df.columns:
            raise MissingColumnError(
                f"Date column '{self.date_column}' not found in DataFrame"
            )

        for idx, raw_value in df[self.date_column].items():
            # 1. אם מדובר ב־NaN / None, לדלג
            if pd.isna(raw_value):
                self.logger.debug(
                    f"Row {idx}: Skipping NaN/None in '{self.date_column}'."
                )
                continue

            # 2. אם זו מחרוזת וללא שום ספרה, לדלג (למשל 'billing')
            if isinstance(raw_value, str) and not any(ch.isdigit() for ch in raw_value):
                self.logger.debug(
                    f"Row {idx}: Skipping non-numeric string '{raw_value}'."
                )
                continue

            # 3. ניסיון המרה
            if not self._is_valid_date(raw_value):
                self.logger.error(
                    f"Row {idx}: Invalid date value '{raw_value}' in column '{self.date_column}'."
                )
                raise InvalidDateError(raw_value)

            self.logger.debug(f"Row {idx}: Valid date '{raw_value}'.")

    def _is_valid_date(self, value) -> bool:
        """
        מנסה להמיר ערך לפורמט תאריך באמצעות pandas.
        אם date_format הוגדר, משתמש בו; אחרת מאפשר חילוץ אוטומטי.

        Args:
            value: הערך לבדיקה (יכול להיות str, datetime, מספרי וכו').

        Returns:
            bool: True אם ניתן להמיר ל־datetime, False אחרת.
        """
        try:
            if self.date_format:
                pd.to_datetime(value, format=self.date_format, errors="raise")
            else:
                pd.to_datetime(value, errors="raise")
            return True
        except Exception:
            return False
