import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, cast
import os
from myapp.utils.date_utils import parse_date_flex, clean_and_parse_dates

import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from myapp.services.mail_utils import send_report_by_email
from flask import current_app

from myapp.services import report_analyzer
from myapp.services.pdf_generator import generate_pdf_report
from myapp.services.email_service import EmailService
from myapp.utils.logger_config import get_logger
from myapp.utils.format_utils import format_currency, format_date
from myapp.utils.validation_utils import validate_uploaded_df
from myapp.utils.dataframe_utils import prepare_pdf_dataframe
from myapp.services.report_analyzer import build_report_data
from myapp.utils.normalizers import normalize_columns

# Configure logger
logger = get_logger(__name__)

# Create console handler if no handlers exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Shared column order for reports
COLUMN_ORDER = [
    "job_id",
    "date",
    "technician",
    "name",
    "phone_code",
    "address",
    "job_type",
    "car_info",
    "notes",
    "amount",
    "parts",
    "payment_method",
    "refund_to_tech",
    "balance_to_client",
]

# Ensure templates directory exists
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "reports"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Configure Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_excel_report(
    jobs: List[Dict[str, Any]], output_dir: str = "output"
) -> Tuple[str, str]:
    """
    Generate an Excel report from a list of job dictionaries.
    Args:
        jobs (List[Dict[str, Any]]): List of job records.
        output_dir (str): Directory where the Excel file will be saved.
    Returns:
        Tuple[str, str]: (full path to the generated Excel file, timestamp used in filename)
    Raises:
        ValueError: If the jobs list is empty.
    """
    if not jobs:
        raise ValueError("No jobs provided for report generation.")
    df = pd.DataFrame(jobs)
    logger.debug("TYPECHECK: %s in generate_excel_report", type(df).__name__)
    df["date"] = df.get("date", "Unknown")
    df["refund_to_tech"] = ((df["amount"] - df["parts"]) * 0.55 + df["parts"]).round(2)
    df["balance_to_client"] = (df["amount"] - df["refund_to_tech"]).round(2)
    column_order = [
        "job_id",
        "date",
        "technician",
        "name",
        "phone_code",
        "address",
        "job_type",
        "car_info",
        "notes",
        "amount",
        "parts",
        "payment_method",
        "refund_to_tech",
        "balance_to_client",
    ]
    df = df[[col for col in column_order if col in df.columns]]
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"autoclose_report_{timestamp}.xlsx"
    file_path = os.path.join(output_dir, filename)
    df.to_excel(file_path, index=False)
    return str(file_path), timestamp


def generate_client_pdf(report_data: dict[str, Any], output_path: str) -> None:
    # הגנה על מפתחות חיוניים
    for key in ["total", "cash", "credit", "parts", "tech_profit"]:
        report_data.setdefault(key, 0)
    tech_name = report_data.get("tech") or report_data.get("technician")
    signature_path: Optional[str]
    if tech_name:
        filename = secure_filename(
            tech_name.split("/")[0].strip().replace(" ", "_") + ".png"
        )
        signature_path = os.path.abspath(os.path.join("static", "signatures", filename))
        if not os.path.exists(signature_path):
            signature_path = None
    else:
        signature_path = None
    template_dir = Path(__file__).resolve().parents[2] / "templates" / "reports"
    env = Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
    )
    template = env.get_template("client_report.html")
    rendered_html = template.render(
        report_data=report_data,
        signature_path=f"file://{signature_path}" if signature_path else None,
    )
    HTML(string=rendered_html, base_url=os.getcwd()).write_pdf(output_path)
    logger.info(f"✅ PDF saved to: {output_path}")


def generate_monthly_summary_pdf(
    records: list[dict[str, Any]], start_date: date, end_date: date
) -> None:
    if not records:
        raise RuntimeError("אין נתונים ליצירת דוח חודשי.")
    try:
        template_dir = Path(__file__).resolve().parents[2] / "templates" / "reports"
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template("monthly_summary_with_graph.html")
        pie_chart = create_pie_chart(records)
        tech_bar_chart = create_technician_bar_chart(records)
        technician_amount_chart = create_technician_amount_bar_chart(records)
        # 🧠 תרגום תאריכים למחרוזות ליצירת שם קובץ
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        output_path = (
            f"static/monthly_reports/monthly_summary_{start_str}_{end_str}.pdf"
        )
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        rendered_html = template.render(
            records=records,
            start=start_date,
            end=end_date,
            pie_chart=pie_chart,
            tech_bar_chart=tech_bar_chart,
            technician_amount_chart=technician_amount_chart,
            now=datetime.now(),
        )
        HTML(string=rendered_html, base_url=os.getcwd()).write_pdf(output_path)
        logger.info(f"✅ דוח חודשי שמור בהצלחה ב: {output_path}")
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת דוח חודשי: {e}", exc_info=True)
        raise


def create_pie_chart(records: list[dict[str, Any]]) -> str:
    from collections import Counter

    job_types = [r.get("job_type", "Unknown") for r in records]
    counts = Counter(job_types)
    labels, values = zip(*counts.items())
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    # Add padding fix for Base64 if needed
    if len(encoded) % 4:
        encoded += "=" * (4 - len(encoded) % 4)
    # בדיקת תקינות base64
    if not encoded.startswith("iVBOR") and not encoded.startswith("/9j/"):
        logger.error("⚠️ PNG base64 image may be corrupted.")
    return f"data:image/png;base64,{encoded}"


def create_technician_bar_chart(records: list[dict[str, Any]]) -> str:
    try:
        if isinstance(records, list):
            df = pd.DataFrame(records)
        elif isinstance(records, pd.DataFrame):
            df = records.copy()
        else:
            raise ValueError(
                "הפורמט של 'records' אינו נתמך. יש לספק רשימת dict או DataFrame."
            )
        if "tech" not in df.columns or df["tech"].isna().all():
            raise ValueError("אין נתוני טכנאי לעיבוד בדוח.")
        technician_counts = df["tech"].value_counts().sort_values(ascending=False)
        plt.figure(figsize=(10, 6), dpi=100)
        ax = technician_counts.plot(kind="bar", edgecolor="black")
        ax.set_title("Number of Jobs per Technician", fontsize=14, pad=12)
        ax.set_xlabel("Technician", fontsize=12)
        ax.set_ylabel("Number of Jobs", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close()
        # Add padding fix for Base64 if needed
        if len(encoded) % 4:
            encoded += "=" * (4 - len(encoded) % 4)
        # בדיקת תקינות base64
        if not encoded.startswith("iVBOR") and not encoded.startswith("/9j/"):
            logger.error("⚠️ PNG base64 image may be corrupted.")
        return f"data:image/png;base64,{encoded}"
    except ValueError as ve:
        logger.error(f"❌ create_technician_bar_chart: נתוני טכנאי לא תקינים - {ve}")
        raise
    except Exception as e:
        logger.error(
            f"❌ create_technician_bar_chart: שגיאה ביצירת גרף טכנאים - {str(e)}"
        )
        raise


def create_technician_amount_bar_chart(records: list[dict[str, Any]]) -> str:
    try:
        if isinstance(records, list):
            df = pd.DataFrame(records)
        elif isinstance(records, pd.DataFrame):
            df = records.copy()
        else:
            raise ValueError(
                "הפורמט של 'records' אינו נתמך. יש לספק רשימת dict או DataFrame."
            )
        if "tech" not in df.columns or df["tech"].isna().all():
            raise ValueError("אין נתוני טכנאי לעיבוד בדוח.")
        technician_amounts = (
            df.groupby("tech")["amount"].sum().sort_values(ascending=False)
        )
        plt.figure(figsize=(10, 6), dpi=100)
        ax = technician_amounts.plot(kind="bar", edgecolor="black")
        ax.set_title("Total Amount per Technician", fontsize=14, pad=12)
        ax.set_xlabel("Technician", fontsize=12)
        ax.set_ylabel("Total Amount", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close()
        # Add padding fix for Base64 if needed
        if len(encoded) % 4:
            encoded += "=" * (4 - len(encoded) % 4)
        # בדיקת תקינות base64
        if not encoded.startswith("iVBOR") and not encoded.startswith("/9j/"):
            logger.error("⚠️ PNG base64 image may be corrupted.")
        return f"data:image/png;base64,{encoded}"
    except ValueError as ve:
        logger.error(
            f"❌ create_technician_amount_bar_chart: נתוני טכנאי לא תקינים - {ve}"
        )
        raise
    except Exception as e:
        logger.error(
            f"❌ create_technician_amount_bar_chart: שגיאה ביצירת גרף סכומים - {str(e)}"
        )
        raise


def get_jobs_by_date(date_str: str) -> list[dict[str, Any]]:
    try:
        file = f"data/{date_str}.xlsx"
        if not os.path.exists(file):
            logger.error(
                f"get_jobs_by_date: Failed to read {file}: file does not exist"
            )
            return []
        df = pd.read_excel(file)
        return df.to_dict("records")
    except Exception as e:
        logger.error(f"get_jobs_by_date: Failed to read {file}: {e}")
        return []


def prepare_client_report_context(report_data: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare the context for client report generation.
    This function adds default values, type checks and logging.
    """
    try:
        if not report_data:
            logger.warning("prepare_client_report_context: Empty report_data provided")
            return {}

        # Ensure all required fields exist with default values
        required_fields = {
            "total": 0,
            "cash": 0,
            "credit": 0,
            "parts": 0,
            "tech_profit": 0,
        }
        for field, default in required_fields.items():
            if field not in report_data or report_data[field] is None:
                report_data[field] = default
                logger.info(
                    f"prepare_client_report_context: Added default value for {field}"
                )

        # Get technician name and handle signature
        tech_name = report_data.get("tech") or report_data.get("technician")
        if tech_name:
            filename = secure_filename(
                tech_name.split("/")[0].strip().replace(" ", "_") + ".png"
            )
            abs_path = os.path.abspath(os.path.join("static", "signatures", filename))
            if os.path.exists(abs_path) and abs_path.lower().endswith(".png"):
                logger.info(f"[ClientReport] Including signature from path: {abs_path}")
                report_data["signature_path"] = f"file://{abs_path}"
            else:
                logger.warning(f"❌ Signature not found or not PNG: {abs_path}")
        else:
            logger.info("[ClientReport] No technician name found for signature.")

        return report_data
    except Exception as e:
        logger.error(
            f"prepare_client_report_context: Error preparing report context - {str(e)}"
        )
        return {}


def create_and_email_report(
    df: pd.DataFrame,
    report_type: str,
    tech_name: str,
    client_id: str
) -> str:
    """
    Creates a PDF report from the given DataFrame and returns the path.
    
    Parameters:
        df (pd.DataFrame): The input data to report.
        report_type (str): A label for the type of report (used in filename).
        tech_name (str): The name of the technician.
        client_id (str): The client identifier.

    Returns:
        str: Full path to the created PDF report.
    """
    logger.debug("TYPECHECK: %s in create_and_email_report", type(df).__name__)
    logger.debug("📨 Running create_and_email_report() from report_utils.py")
    logger.info("📄 יצירת דוח: type=%s, tech=%s, client=%s", report_type, tech_name, client_id)

    # Validate + Prepare
    from myapp.utils.validation_utils import validate_uploaded_df
    from myapp.utils.dataframe_utils import prepare_pdf_dataframe

    df = validate_uploaded_df(df)
    df = prepare_pdf_dataframe(df)
    assert isinstance(df, pd.DataFrame), "create_and_email_report must return a DataFrame after preparation"

    # Clean and parse date columns safely before analysis
    date_cols = [col for col in ["date", "closed", "created"] if col in df.columns]
    if date_cols:
        logger.info(f"🕒 מנקה וממפה עמודות תאריך: {date_cols}")
        df = clean_and_parse_dates(df, date_cols)
    else:
        logger.warning("⚠️ לא נמצאו עמודות תאריך לניקוי ב-DataFrame!")

    # Analyze
    df = normalize_columns(df)
    if "job_id" not in df.columns:
        df["job_id"] = [f"A{i+1}" for i in range(len(df))]
    print("🧪 עמודות אחרי normalize_columns:", df.columns.tolist())
    print(df[["tech", "technician"]].head())
    detail_df, summaries = build_report_data(df)
    assert isinstance(detail_df, pd.DataFrame), "build_report_data must return a DataFrame as first element"

    # Generate report
    report_path = generate_pdf_report(
        df=detail_df,
        report_type=report_type,
        extra={"tech_name": tech_name, "client_id": client_id}
    )

    logger.info("✅ דוח נוצר: %s", report_path)
    return str(report_path)
