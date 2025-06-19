"""
Business‑layer: financial analysis on job records.

Workflow
========
1.  load_jobs_excel()   -> Raw DataFrame from Excel / CSV.
2.  clean_and_cast()    -> Fix types, parse dates, numeric casts.
3.  enrich_financials() -> Adds computed cols (net_income, gross_profit, etc.).
4.  summarise()         -> Returns dict of summary DataFrames / dicts.
5.  build_report_data() -> Packs everything for the export layer.

This file **knows nothing about PDF/Excel**.  Export happens in
pdf_generator.py / export_utils.py — we just hand over DataFrames.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import logging

from myapp.finance.rules import load_commission_rules
from myapp.finance.calculator import resolve_commission
from myapp.services.pdf_generator import generate_pdf_report
from myapp.services.email_service import EmailService
from myapp.utils.logger_config import get_logger
from myapp.utils.dataframe_utils import coerce_dates
from myapp.utils.decimal_utils import apply_safe_decimal
from myapp.utils.sanitize_uploaded_dataframe import sanitize_uploaded_dataframe
from myapp.utils.validation_utils import validate_uploaded_df
from myapp.utils.date_utils import clean_and_parse_dates

logger = logging.getLogger(__name__)
EXPORT_FOLDER = Path("output/reports_exported")

# ------------------------------------------------------------------------------
# 1. Loading
# ------------------------------------------------------------------------------


def load_jobs_excel(path: str, sheet: Optional[str] = None) -> pd.DataFrame:
    """
    Read Excel/CSV into DataFrame with raw strings preserved.
    Supported:
        - .xlsx / .xls  (openpyxl)
        - .csv
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    ext = os.path.splitext(path)[1].lower()
    if ext in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif ext == ".csv":
        df = pd.read_csv(path, dtype=str)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return df


# ------------------------------------------------------------------------------
# 2. Cleaning & casting helpers
# ------------------------------------------------------------------------------

_DATE_COLS = ["created", "date", "closed"]
_FLOAT_COLS = [
    "total",
    "cash",
    "credit",
    "billing",
    "check",
    "tip_amount",
    "parts",
    "company_parts",
    "tech_profit",
    "balance_tech",
]


def _to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="%m/%d/%Y %I:%M %p")


def _to_float(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True).replace("", np.nan)
    )
    return cleaned.astype(float)


def clean_and_cast(df: pd.DataFrame) -> pd.DataFrame:
    logger.debug("TYPECHECK: %s in clean_and_cast", type(df).__name__)
    """Casts dates & numerics, trims spaces, standardises column names."""
    df = df.copy()

    # ⇢ Standard column names (lower snake_case)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ⇢ Dates
    for col in _DATE_COLS:
        if col in df.columns:
            df[col] = _to_datetime(df[col])

    # ⇢ Numerics
    for col in _FLOAT_COLS:
        if col in df.columns:
            df[col] = _to_float(df[col])

    # tech_share "50%" ⇒ 0.5
    if "tech_share" in df.columns:
        df["tech_share"] = (
            df["tech_share"]
            .astype(str)
            .str.replace("%", "")
            .replace("", np.nan)
            .astype(float)
            .div(100)
        )

    # payment_method (derive best‑guess)
    if "payment_method" not in df.columns:
        df["payment_method"] = np.select(
            [
                df["cash"].gt(0),
                df["credit"].gt(0),
                df["check"].gt(0),
                df["billing"].gt(0),
            ],
            ["cash", "credit", "check", "billing"],
            default="unknown",
        )

    return df


# ------------------------------------------------------------------------------
# 3. Enrichment / business rules
# ------------------------------------------------------------------------------

_HIGH_COMM = Decimal("0.75")  # 75 %
_FLAGS_COLS: List[str] = ["parts_flag", "net_flag", "commission_flag", "duration_flag"]


def enrich_financials(df: pd.DataFrame) -> pd.DataFrame:
    logger.debug("TYPECHECK: %s in enrich_financials", type(df).__name__)
    """
    חישוב רווחים, flag חריגים, וניקוי תאריכים וערכים כספיים – בבטחה.
    """
    logger.debug("🧾 df.columns: %s", df.columns.tolist())

    # 🕒 ניקוי תאריכים – רק אם קיימים
    date_cols = [col for col in ["date", "closed", "created"] if col in df.columns]
    if date_cols:
        logger.info(f"🕒 מנקה וממפה עמודות תאריך ב־enrich: {date_cols}")
        df = clean_and_parse_dates(df, date_cols)
    else:
        logger.warning("⚠️ אין עמודות תאריך זמינות ב־DataFrame בעת enrich")

    # 💸 המרה בטוחה של עמודות כספיות
    df["tech_cut"] = apply_safe_decimal(df, "tech_cut")
    df["total"] = apply_safe_decimal(df, "total")

    # 💸 חישוב net_income = total - tech_cut (אם שניהם קיימים)
    try:
        df["net_income"] = df["total"] - df["tech_cut"]
    except Exception as e:
        logger.warning(f"⚠️ חישוב net_income נכשל: {e}")
        df["net_income"] = None

    # 💸 חישוב company_net – חכם: אם יש net_income, השתמש בו, אחרת חישוב ישיר
    try:
        df["company_net"] = df["net_income"]
    except Exception:
        try:
            df["company_net"] = df["total"] - df["tech_cut"]
        except Exception as e:
            logger.warning(f"⚠️ חישוב company_net נכשל: {e}")
            df["company_net"] = None

    # 🧠 חישוב דגלים – רק אם העמודות לא NaN
    try:
        mask = (df["total"] > 0) & (df["tech_cut"] / df["total"] > _HIGH_COMM)
        df["flag"] = np.where(mask, "HIGH", "")
    except Exception as e:
        logger.warning(f"⚠️ שגיאה בחישוב flag HIGH COMMISSION: {e}")

    return df


# ------------------------------------------------------------------------------
# 4. Summaries
# ------------------------------------------------------------------------------


def summarise(df: pd.DataFrame) -> dict:
    summary = {}
    overall = pd.DataFrame(
        {
            "metric": [
                "jobs",
                "total_income",
                "parts_cost",
                "net_income",
                "company_net",
            ],
            "value": [
                len(df),
                df["total"].sum(),
                df["parts"].sum(),
                df["net_income"].sum(),
                df["company_net"].sum(),
            ],
        }
    )
    summary["overall"] = overall

    if "payment_method" in df.columns:
        summary["by_payment"] = df.groupby("payment_method", dropna=False)["total"].sum().to_dict()
    else:
        summary["by_payment"] = {}

    by_tech = (
        df.groupby("tech", dropna=False)["total"].sum().rename("total").reset_index()
    )
    summary["by_tech"] = by_tech

    by_service = (
        df.groupby("job_type", dropna=False)
        .agg(jobs=("total", "size"), income=("total", "sum"))
        .reset_index()
    )
    summary["by_service"] = by_service

    # Daily summary with protection
    if "date" not in df.columns or df["date"].dropna().empty:
        logger.warning("⚠️ עמודת 'date' ריקה או לא קיימת – לא ניתן לבצע resample יומי.")
        daily = pd.DataFrame(columns=["date", "total"])
    else:
        daily = (
            df.set_index("date")
            .resample("D")["total"]
            .agg(jobs=("size"), income=("sum"))
            .reset_index()
        )
    summary["daily"] = daily

    return summary


def get_kpi_summary(df: pd.DataFrame) -> dict[str, float | int | list]:
    """
    Computes business KPIs from enriched DataFrame.

    Returns:
        {
            total_income: float,
            total_jobs: int,
            average_per_job: float,
            gross_profit: float,
            technicians: list[dict]  # List of technician performance data
        }
    """
    if df.empty:
        return {
            "total_income": 0.0,
            "total_jobs": 0,
            "average_per_job": 0.0,
            "gross_profit": 0.0,
            "technicians": [],
        }

    # Calculate overall metrics
    total_income = df["total"].sum()
    total_jobs = len(df)
    average_per_job = total_income / total_jobs if total_jobs > 0 else 0.0
    gross_profit = (
        df["net_income"].sum() if "net_income" in df.columns else total_income
    )

    # Calculate technician performance
    tech_performance = []
    if "tech" in df.columns:
        tech_groups = df.groupby("tech")
        for tech_name, tech_df in tech_groups:
            tech_income = tech_df["total"].sum()
            tech_jobs = len(tech_df)
            tech_profit = (
                tech_df["net_income"].sum()
                if "net_income" in tech_df.columns
                else tech_income
            )
            tech_avg = tech_income / tech_jobs if tech_jobs > 0 else 0.0

            tech_performance.append(
                {
                    "name": tech_name,
                    "jobs_count": tech_jobs,
                    "income": float(round(tech_income, 2)),
                    "profit": float(round(tech_profit, 2)),
                    "average_per_job": float(round(tech_avg, 2)),
                }
            )

    return {
        "total_income": float(round(total_income, 2)),
        "total_jobs": total_jobs,
        "average_per_job": float(round(average_per_job, 2)),
        "gross_profit": float(round(gross_profit, 2)),
        "technicians": tech_performance,
    }


# ------------------------------------------------------------------------------
# 5. Orchestrator – single public API
# ------------------------------------------------------------------------------


def expand_multi_tech_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expands jobs with multiple technicians into separate rows per tech.
    """
    df = df.copy()
    rows = []

    for _, row in df.iterrows():
        techs = str(row.get("tech", "")).split("/")
        shares_raw = (
            str(row.get("tech_share", "")).split("/") if "tech_share" in row else []
        )

        if len(techs) == 1:
            rows.append(row)
            continue

        num_techs = len(techs)

        # Calculate individual shares
        if len(shares_raw) == num_techs:
            shares = [float(s.strip().replace("%", "")) / 100 for s in shares_raw]
        else:
            shares = [1 / num_techs] * num_techs

        for tech, share in zip(techs, shares):
            new_row = row.copy()
            new_row["tech"] = tech.strip()
            new_row["tech_share"] = share
            rows.append(new_row)

    return pd.DataFrame(rows)


def get_report_dataframe(
    data,
    *,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Validate, clean and transform uploaded report data before reporting logic.
    """
    if isinstance(data, pd.DataFrame):
        df = validate_uploaded_df(data.copy())
        df = coerce_dates(df, ["date", "closed", "created_at", "updated_at"])
        df = enrich_financials(df)
        print("✅ אחרי validate_uploaded_df: ", df.shape)
    else:
        df = load_jobs_excel(data)
        df = clean_and_cast(df)
        df = expand_multi_tech_jobs(df)
        df = coerce_dates(df, ["date", "closed", "created_at", "updated_at"])
        df = enrich_financials(df)
    if date_from:
        df = df[df["date"] >= pd.Timestamp(date_from)]
    if date_to:
        df = df[df["date"] <= pd.Timestamp(date_to)]
    if tech_filter:
        df = df[df["tech"].isin(tech_filter)]
    if service_filter:
        df = df[df["job_type"].isin(service_filter)]
    assert isinstance(df, pd.DataFrame), "get_report_dataframe must return a DataFrame"
    return df


def get_report_summary(
    excel_path: str,
    *,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Loads, cleans, expands, enriches, and filters job data, returning only the summary DataFrame grouped by 'tech'.
    """
    df, summaries = build_report_data(
        excel_path,
        date_from=date_from,
        date_to=date_to,
        tech_filter=tech_filter,
        service_filter=service_filter,
    )
    by_tech = df.groupby("tech", dropna=False).sum(numeric_only=True).reset_index()
    return by_tech


def build_report_data(
    data,
    *,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
):
    df = get_report_dataframe(
        data,
        date_from=date_from,
        date_to=date_to,
        tech_filter=tech_filter,
        service_filter=service_filter,
    )
    required_cols = ["total", "parts", "date", "closed"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"שדות חסרים בקובץ: {missing}")
    # For compatibility, return (df, summaries) if called from report_utils
    summaries = summarise(df)
    assert isinstance(df, pd.DataFrame), "build_report_data must return a DataFrame as first element"
    return df, summaries


def get_tech_summary(
    excel_path: str,
    *,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
) -> dict[str, pd.DataFrame]:
    df, _ = build_report_data(
        excel_path,
        date_from=date_from,
        date_to=date_to,
        tech_filter=tech_filter,
        service_filter=service_filter,
    )
    return {"by_tech": df}


def analyze_report(df: pd.DataFrame, report_type: str) -> str:
    """
    מבצע אנליזה על DataFrame, מייצר PDF, שומר, ושולח במייל.
    מחזיר output_id עבור tracking.
    """

    output_id = f"{datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')}_{report_type}_{uuid4().hex[:8]}"
    filename = f"{output_id}.pdf"
    output_path = EXPORT_FOLDER / filename

    EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    logger.info("Generating PDF report: %s", output_path)

    generate_pdf_report(df=df, output_path=str(output_path))

    # שליחה במייל
    emailer = EmailService()
    attachment_path = (
        output_path if not isinstance(output_path, str) else Path(output_path)
    )
    emailer.send(
        to="manager@yourcompany.com",  # תחליף לפי הצורך
        subject=f"AutoClose Report: {report_type}",
        body="Attached is the generated report.",
        attachment=attachment_path,
    )

    return "OK"


def get_income_trend_from_df(df: pd.DataFrame) -> list[dict[str, str | float]]:
    """
    Returns list [{"date": "YYYY-MM-DD", "income": 123.45, "jobs": N}, ...], sorted asc.
    Rounds income to 2 decimals.
    """
    if df.empty or {"date", "total"} - set(df.columns):
        return []
    grouped = (
        df.assign(date=df["date"].dt.strftime("%Y-%m-%d"))
          .groupby("date", as_index=False)
          .agg(income=("total", "sum"), jobs=("total", "count"))
          .round({"income": 2})
    )
    return grouped.to_dict("records")


def get_income_trend(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    df, summaries = build_report_data(path)
    return get_income_trend_from_df(df)
