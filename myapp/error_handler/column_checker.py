from myapp.utils.logger_config import get_logger

logger = get_logger(__name__)
import logging
from typing import Dict, List, Optional
import pandas as pd
from .base import MissingColumnError


class ColumnChecker:
    """
    Validates that a DataFrame contains all required columns, supporting alternative names
    and optional case-insensitive matching.

    required_columns: dict where
        key = logical column name (str),
        value = list of alternative column names (List[str]) to check in the DataFrame.

    Usage:
        checker = ColumnChecker(
            {
                "user_id": ["UserID", "user_id", "ID"],
                "amount": ["Amt", "Amount", "amt"]
            },
            case_insensitive=True
        )
        mapping = checker.check(df)
        # mapping: {"user_id": "UserID", "amount": "Amount"}
    """

    def __init__(
        self,
        required_columns: Dict[str, List[str]],
        case_insensitive: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Args:
            required_columns: dict[str, list[str]]
                מגדיר עמודות נדרשות: כל key הוא שם לוגי, כל value היא רשימת שמות חלופיים אפשריים.
            case_insensitive: bool
                אם True, מבצעים חיפוש עמודות ללא תלות באותיות רישיות/קטנות.
            logger: logging.Logger | None
                אם לא None, ישתמשו בלוגר הזה להדפסת הודעות debug על התאמות.
        """
        self.required_columns = required_columns
        self.case_insensitive = case_insensitive
        self.logger = logger or logging.getLogger(__name__)

    def check(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        בודק שכל ה־logical_names קיימים ב־DataFrame (לפחות תחת אחת מהחלופות).

        Args:
            df: pandas.DataFrame - טבלת הנתונים שיש לבדוק בה עמודות.

        Returns:
            Dict[str, str]: מיפוי של שם עמודה לוגי → השם האמיתי שנמצא ב־df.

        Raises:
            MissingColumnError: אם לא נמצא שם עמודה (לא אחת מהחלופות) עבור כל ה־logical_names.
                ההודעה תכלול את כל השמות הלוגיים החסרים.
        """
        actual_columns = list(df.columns)
        matched: Dict[str, str] = {}
        missing_keys: List[str] = []

        # להכין רשימה של עמודות בפורמט התאם אם צריך
        if self.case_insensitive:
            normalized_actual = {col.lower(): col for col in actual_columns}
        else:
            normalized_actual = {col: col for col in actual_columns}

        for logical_name, alternatives in self.required_columns.items():
            found_name: Optional[str] = None

            for alt in alternatives:
                if self.case_insensitive:
                    alt_key = alt.lower()
                    if alt_key in normalized_actual:
                        found_name = normalized_actual[alt_key]
                        break
                else:
                    if alt in normalized_actual:
                        found_name = alt
                        break

            if found_name is None:
                missing_keys.append(logical_name)
            else:
                matched[logical_name] = found_name
                self.logger.debug(
                    f"Matched logical '{logical_name}' → actual '{found_name}'"
                )

        if missing_keys:
            # מצרפים את כל השמות הלוגיים החסרים להודעה אחת
            missing_str = ", ".join(missing_keys)
            raise MissingColumnError(
                f"Missing required columns for logical names: {missing_str}"
            )

        return matched

        return matched
