import pandas as pd
import pytest
from myapp.services.pdf_generator import _prepare_pdf_dataframe


def test_prepare_pdf_dataframe_full_flow():
    df = pd.DataFrame([
        {"job_id": "J1", "total": 200, "parts": 50, "tech_share": "50%", "date": "2025-06-01 10:00", "closed": "2025-06-01 12:00"},
        {"job_id": "J2", "total": 100, "parts": 20, "tech_share": "50%", "date": "2025-06-02 09:00", "closed": "2025-06-02 10:00"},
    ])
    
    format_cols = ["total", "parts", "tech_cut", "company_net"]
    result_df = _prepare_pdf_dataframe(df, format_columns=format_cols)

    # בדיקה ששורת totals נוספה
    assert result_df.iloc[0]["job_id"].startswith("Totals:")

    # בדיקה שעבר enrichment
    assert "tech_cut" in result_df.columns
    assert "company_net" in result_df.columns

    # בדיקה לעיצוב סכומים (תוצאה כסטרינג עם פורמט)
    assert result_df.loc[0, "total"].endswith("00")  # לדוגמה: '300.00'

    # בדיקה שאין עמודות חסרות
    for col in format_cols:
        assert col in result_df.columns
