from .base import DataSanitizationError


class ValueSanitizer:
    """
    Checks for invalid characters in specified string fields.
    Ignores missing fields gracefully.
    """

    def __init__(self, fields_to_check, invalid_chars="@#$%^&*"):
        self.fields = fields_to_check  # רשימה של שמות עמודות לבדיקה
        self.invalid_chars = set(invalid_chars)  # קבוצת תווים אסורים

    def check(self, df):
        for field in self.fields:
            if field not in df.columns:
                continue  # אם העמודה לא קיימת ב־DataFrame, מדלגים עליה
            for value in df[field]:
                # ממירים כל ערך למחרוזת ומחפשים תווים אסורים
                if any(char in str(value) for char in self.invalid_chars):
                    raise DataSanitizationError(field, value)
