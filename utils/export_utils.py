import os
import re
import logging
from datetime import date, datetime

import pandas as pd

def export_monthly_summary_csv(records: pd.DataFrame, start_date, end_date, output_folder: str = "static/monthly_reports") -> str:
    """
    מייצרת קובץ CSV של רשומות שירות עבור טווח תאריכים נתון ושומרת אותו בתיקיית reports החודשיים.

    Args:
        records (pd.DataFrame): DataFrame מסונן של רשומות שירות.
        start_date (str | date | datetime): תאריך תחילת התקופה (מחרוזת או אובייקט date/datetime).
        end_date (str | date | datetime): תאריך סיום התקופה (מחרוזת או אובייקט date/datetime).
        output_folder (str): נתיב לתיקייה שבה ישמר הקובץ (ברירת מחדל: "static/monthly_reports").

    Returns:
        str: הנתיב המלא של קובץ ה-CSV שנוצר.

    Raises:
        ValueError: אם ה-records אינו DataFrame או אם אין בו שורות.
        RuntimeError: אם התרחשה שגיאה בשמירת הקובץ.
    """
    # אימות סוג הנתונים
    if not isinstance(records, pd.DataFrame):
        logging.error("export_monthly_summary_csv: 'records' חייב להיות pandas DataFrame.")
        raise ValueError("'records' חייב להיות pandas DataFrame.")
    if records.empty:
        logging.error("export_monthly_summary_csv: DataFrame ריק, אין נתונים לשמירה.")
        raise ValueError("אין נתונים לשמירה (DataFrame ריק).")

    # המרת תאריכים למחרוזת אחידה (YYYY-MM-DD)
    def _format_date(obj):
        if isinstance(obj, (date, datetime)):
            return obj.strftime("%Y-%m-%d")
        return str(obj)

    start_str = _format_date(start_date)
    end_str = _format_date(end_date)

    print(f"START: {start_date} (type: {type(start_date)}), END: {end_date} (type: {type(end_date)})")
    print(f"start_str: {start_str}, end_str: {end_str}")

    # יצירת תיקיית היעד במידת הצורך
    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        logging.error(f"export_monthly_summary_csv: לא ניתן ליצור את התיקייה '{output_folder}' - {e}", exc_info=True)
        raise RuntimeError(f"לא ניתן ליצור את התיקייה '{output_folder}'.") from e

    # בניית שם הקובץ תוך הסרת תווים בלתי רצויים
    raw_filename = f"monthly_summary_{start_str}_{end_str}.csv"
    # מחליף כל תו שאינו אות, ספרה, קו תחתון או מקף ב־מקף
    safe_filename = re.sub(r"[^\w\-]+", "-", raw_filename)
    output_path = os.path.join(output_folder, safe_filename)

    # שמירת ה-CSV
    try:
        records.to_csv(output_path, index=False)
        logging.info(f"✅ קובץ CSV שמור ב: {output_path}")
    except Exception as e:
        logging.error(f"export_monthly_summary_csv: שגיאה בשמירת הקובץ ל־'{output_path}' - {e}", exc_info=True)
        raise RuntimeError(f"שגיאה בשמירת קובץ ה-CSV: {e}") from e

    return output_path 