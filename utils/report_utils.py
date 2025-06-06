import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, cast
import os

import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from werkzeug.utils import secure_filename

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


def generate_pdf_report(
    jobs: List[Dict[str, Any]], output_dir: str = "output"
) -> Tuple[str, str]:
    """
    Generate a PDF report from a list of job dictionaries using HTML and WeasyPrint.
    Args:
        jobs (List[Dict[str, Any]]): List of structured job records.
        output_dir (str): Directory where the PDF file will be saved (default: "output").
    Returns:
        Tuple[str, str]: (full path to the generated PDF file, timestamp used in filename).
    Raises:
        ValueError: If the jobs list is empty.
    """
    if not jobs:
        raise ValueError("No jobs provided for PDF generation.")
    html_template = """
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          h1 { color: #2c3e50; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ccc; padding: 8px; font-size: 12px; text-align: left; }
          th { background-color: #f2f2f2; }
        </style>
      </head>
      <body>
        <h1>AutoClose – Technician Job Report</h1>
        <table>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Date</th>
              <th>Technician</th>
              <th>Name</th>
              <th>Amount</th>
              <th>Parts</th>
              <th>Refund</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            {% for job in jobs %}
            <tr>
              <td>{{ job.job_id }}</td>
              <td>{{ job.date or 'Unknown' }}</td>
              <td>{{ job.technician or '' }}</td>
              <td>{{ job.name or '' }}</td>
              <td>${{ '%.2f'|format(job.amount or 0) }}</td>
              <td>${{ '%.2f'|format(job.parts or 0) }}</td>
              <td>
                ${{
                    '%.2f'|format(
                        ((job.amount or 0) - (job.parts or 0)) * 0.55 + (job.parts or 0)
                    )
                }}
              </td>
              <td>
                ${{
                    '%.2f'|format(
                        (job.amount or 0) - (
                            ((job.amount or 0) - (job.parts or 0)) * 0.55 + (job.parts or 0)
                        )
                    )
                }}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </body>
    </html>
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"autoclose_report_{timestamp}.pdf"
    file_path = output_path / filename
    template = Template(html_template)
    rendered_html = template.render(jobs=jobs)
    HTML(string=rendered_html).write_pdf(str(file_path))
    logging.info(f"✅ PDF saved to: {str(file_path)}")
    return str(file_path), timestamp


def generate_client_pdf(report_data: dict, output_path: str) -> None:
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
    env = Environment(
        loader=FileSystemLoader("templates"), autoescape=select_autoescape()
    )
    template = env.get_template("reports/client_report.html")
    rendered_html = template.render(
        report_data=report_data,
        signature_path=f"file://{signature_path}" if signature_path else None,
    )
    HTML(string=rendered_html, base_url=os.getcwd()).write_pdf(output_path)
    logging.info(f"✅ PDF saved to: {output_path}")


def generate_monthly_summary_pdf(
    records: list[dict[str, Any]], start_date: date, end_date: date
) -> None:
    if not records:
        raise RuntimeError("אין נתונים ליצירת דוח חודשי.")
    try:
        env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
        template = env.get_template("reports/monthly_summary_with_graph.html")
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
        logging.info(f"✅ דוח חודשי שמור בהצלחה ב: {output_path}")
    except Exception as e:
        logging.error(f"❌ שגיאה ביצירת דוח חודשי: {e}", exc_info=True)
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
        logging.error("⚠️ PNG base64 image may be corrupted.")
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
        ax.tick_params(axis="x", rotation=45, labelsize=10)
        ax.tick_params(axis="y", labelsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        # Add padding fix for Base64 if needed
        if len(chart_base64) % 4:
            chart_base64 += "=" * (4 - len(chart_base64) % 4)
        # בדיקת תקינות base64
        if not chart_base64.startswith("iVBOR") and not chart_base64.startswith("/9j/"):
            logging.error("⚠️ PNG base64 image may be corrupted.")
        return f"data:image/png;base64,{chart_base64}"
    except ValueError as ve:
        logging.error(f"❌ create_technician_bar_chart: נתוני טכנאי לא תקינים - {ve}")
        raise
    except Exception as e:
        logging.error(
            f"❌ create_technician_bar_chart: שגיאה ביצירת תרשים העמודות - {e}",
            exc_info=True,
        )
        raise RuntimeError("אירעה שגיאה ביצירת תרשים העמודות של הטכנאים.") from e


def create_technician_amount_bar_chart(records: list[dict[str, Any]]) -> str:
    """
    Create a bar chart showing total amount per technician.
    Returns a base64-encoded PNG image.
    """
    try:
        df = pd.DataFrame(records)
        if "tech" not in df.columns or df["tech"].isna().all():
            raise ValueError("No technician data found.")
        if "amount" not in df.columns or df["amount"].isna().all():
            raise ValueError("No amount data found.")
        totals = df.groupby("tech")["amount"].sum().sort_values(ascending=False)
        plt.figure(figsize=(10, 6), dpi=100)
        ax = totals.plot(kind="bar", color="skyblue", edgecolor="black")
        ax.set_title("Total Amount per Technician", fontsize=14)
        ax.set_xlabel("Technician")
        ax.set_ylabel("Total Amount")
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        if len(img_base64) % 4:
            img_base64 += "=" * (4 - len(img_base64) % 4)
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logging.error(
            f"❌ Failed to generate technician amount chart: {e}", exc_info=True
        )
        raise RuntimeError("Technician amount bar chart failed.")


def get_jobs_by_date(date_str: str) -> list[dict[str, Any]]:
    import pandas as pd
    from pathlib import Path

    base_dir = Path("output") / date_str
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    for file in base_dir.iterdir():
        if file.suffix.lower() in {".xlsx", ".csv"}:
            try:
                if file.suffix.lower() == ".xlsx":
                    df = pd.read_excel(file)
                else:
                    df = pd.read_csv(file)
                jobs = df.to_dict(orient="records")
                # ודא שכל המפתחות הם str
                jobs = [{str(k): v for k, v in job.items()} for job in jobs]
                return cast(list[dict[str, Any]], jobs)
            except Exception as e:
                logging.error(f"get_jobs_by_date: Failed to read {file}: {e}")
                return []
    return []


def prepare_client_report_context(report_data: dict) -> dict:
    """
    Prepare and validate context for client_report.html template,
    keep original keys for backward compatibility,
    add default values, type checks and logging.
    """
    context = {}

    # שדות חובה שחשוב לוודא שקיימים
    mandatory_fields = ["customer_name", "date", "job_id", "total"]
    for field in mandatory_fields:
        val = report_data.get(field)
        if not val:
            logging.warning(
                f"[ClientReport] Missing mandatory field '{field}' in report data."
            )
        context[field] = val if val else "N/A"

    # שדות מספריים עם טיפול None וטיפוס שגוי
    numeric_fields = ["total", "cash", "credit", "parts", "tech_profit"]
    for field in numeric_fields:
        val = report_data.get(field)
        if val is None:
            logging.info(
                f"[ClientReport] Payment field '{field}' is None, defaulting to 0.0."
            )
            context[field] = 0.0
        elif not isinstance(val, (int, float)):
            logging.error(
                f"[ClientReport] Payment field '{field}' expected numeric but got {type(val)}. "
                f"Coercing to 0.0."
            )
            context[field] = 0.0
        else:
            context[field] = val

    # שדות אופציונליים שיכולים להיות מחרוזות או None
    optional_fields = [
        "phone",
        "address",
        "tech_share",
        "billing",
        "check",
        "company_parts",
        "balance_tech",
        "tech",
        "technician",
        "job_type",
        "vehicle",
        "key_note",
        "closed",
        "company_name",
    ]
    for field in optional_fields:
        val = report_data.get(field)
        context[field] = val if val else "N/A"

    # הכנת נתיב חתימה
    tech_name = report_data.get("tech") or report_data.get("technician")
    signature_path = None
    if tech_name:
        from werkzeug.utils import secure_filename

        filename = secure_filename(
            tech_name.split("/")[0].strip().replace(" ", "_") + ".png"
        )
        abs_path = os.path.abspath(os.path.join("static", "signatures", filename))
        if os.path.exists(abs_path) and abs_path.lower().endswith(".png"):
            signature_path = f"file://{abs_path}"
            logging.info(f"[ClientReport] Including signature from path: {abs_path}")
        else:
            logging.warning(f"❌ Signature not found or not PNG: {abs_path}")
    else:
        logging.info("[ClientReport] No technician name found for signature.")

    context["signature_path"] = signature_path

    return context
