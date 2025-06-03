# utils/report_utils.py

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import logging
from io import BytesIO
import base64
from werkzeug.utils import secure_filename

import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader
from weasyprint import HTML
import matplotlib.pyplot as plt

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

    Steps:
      1. Convert the job list into a pandas DataFrame.
      2. Normalize missing dates to 'Unknown'.
      3. Calculate:
         - refund_to_tech = (amount - parts) * 0.55 + parts
         - balance_to_client = amount - refund_to_tech
      4. Reorder columns for readability using COLUMN_ORDER.
      5. Ensure the output directory exists.
      6. Save the DataFrame to an Excel file named with a timestamp.

    Args:
        jobs (List[Dict[str, Any]]): List of structured job records.
        output_dir (str): Directory where the Excel file will be saved (default: "output").

    Returns:
        Tuple[str, str]: (full path to the generated Excel file, timestamp used in filename).

    Raises:
        ValueError: If the jobs list is empty.
    """
    if not jobs:
        raise ValueError("No jobs provided for report generation.")

    # Convert job records into a DataFrame
    df = pd.DataFrame(jobs)

    # Normalize missing 'date' entries
    if "date" in df.columns:
        df["date"] = df["date"].fillna("Unknown")

    # Compute refund and balance columns
    df["refund_to_tech"] = (
        (df["amount"] - df["parts"]) * 0.55 + df["parts"]
    ).round(2)
    df["balance_to_client"] = (df["amount"] - df["refund_to_tech"]).round(2)

    # Reorder columns using shared COLUMN_ORDER
    df = df[COLUMN_ORDER]

    # Ensure the output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build timestamp and filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"autoclose_report_{timestamp}.xlsx"
    file_path = output_path / filename

    # Save DataFrame to Excel
    df.to_excel(file_path, index=False)

    return str(file_path), timestamp


def generate_pdf_report(
    jobs: List[Dict[str, Any]], output_dir: str = "output"
) -> Tuple[str, str]:
    """
    Generate a PDF report from a list of job dictionaries using HTML and WeasyPrint.

    Steps:
      1. Validate that jobs list is not empty.
      2. Build a simple HTML string with inline CSS and Jinja2 placeholders.
      3. Ensure the output directory exists.
      4. Render HTML with job data.
      5. Convert rendered HTML to PDF and save with the same timestamp format.

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

    # Basic HTML template with inline styling
    html_template = """
    <html>
      <head>
        <meta charset="utf-8" />
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
                ${{ '%.2f'|format(((job.amount or 0) - (job.parts or 0)) * 0.55 + (job.parts or 0)) }}
              </td>
              <td>
                ${{ '%.2f'|format((job.amount or 0) - (((job.amount or 0) - (job.parts or 0)) * 0.55 + (job.parts or 0))) }}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </body>
    </html>
    """

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build timestamp and filename (same format as Excel)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"autoclose_report_{timestamp}.pdf"
    file_path = output_path / filename

    # Render HTML with job data
    template = Template(html_template)
    rendered_html = template.render(jobs=jobs)

    # Generate PDF file
    HTML(string=rendered_html).write_pdf(str(file_path))

    return str(file_path), timestamp


def generate_client_pdf(report_data: dict, output_path: str) -> None:
    """
    Generates a PDF report for a client based on a template and data.

    Args:
        report_data (dict): Dictionary with all fields (name, date, vehicle, etc.)
        output_path (str): Full path to save the generated PDF
    """
    tech_name = report_data.get("tech") or report_data.get("technician")
    if tech_name:
        filename = secure_filename(tech_name.split("/")[0].strip().replace(" ", "_") + ".png")
        candidate_path = f"static/signatures/{filename}"
        signature_path = candidate_path if os.path.exists(candidate_path) else None
    else:
        signature_path = None

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("reports/client_report.html")
    rendered_html = template.render(report_data, signature_path=signature_path)

    # Generate PDF
    HTML(string=rendered_html).write_pdf(output_path)

    print(f"✅ PDF saved to: {output_path}")


def generate_monthly_summary_pdf(records, start_date, end_date, output_path):
    """
    Generates a monthly summary PDF that includes:
      - A pie chart of service types
      - A bar chart showing number of services per technician
      - An accessible HTML layout rendered to PDF

    Args:
        records (list[dict]): רשימת רשומות שירות, כשכל רשומה מכילה שדה 'technician' ושדות נוספים לצורך הדוח.
        start_date (date | str): תאריך תחילת התקופה (פורמט ISO או אובייקט date).
        end_date (date | str): תאריך סיום התקופה (פורמט ISO או אובייקט date).
        output_path (str): הנתיב המלא לשמירת קובץ ה-PDF הנוצר.

    Raises:
        RuntimeError: במידה שאין רשומות ליצירת הדוח או כשל בכתיבת ה-PDF.
    """
    if not records:
        raise RuntimeError("אין נתונים ליצירת דוח חודשי.")

    try:
        # Load template
        env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=True
        )
        template = env.get_template("reports/monthly_summary_with_graph.html")

        # יצירת גרף עוגה
        pie_chart = create_pie_chart(records)

        # יצירת גרף עמודות של טכנאים
        tech_bar_chart = create_technician_bar_chart(records)

        # העברת כל המשתנים לתבנית
        rendered_html = template.render(
            records=records,
            start=start_date,
            end=end_date,
            pie_chart=pie_chart,            # תמונת Pie chart ב־Base64
            tech_bar_chart=tech_bar_chart,   # תמונת Bar chart ב־Base64
            now=datetime.now()               # 🟢 חדש
        )

        # הפקת PDF מה־HTML המוטמע
        HTML(string=rendered_html).write_pdf(output_path)

        logging.info(f"✅ דוח חודשי שמור בהצלחה ב: {output_path}")

    except Exception as e:
        logging.error(f"❌ שגיאה ביצירת דוח חודשי: {e}", exc_info=True)
        raise


def create_pie_chart(records):
    """
    Create a base64-encoded pie chart showing total job count per job type.
    Returns:
        str: Base64 string to embed as <img src="...">
    """
    from collections import Counter
    job_types = [r.get("job_type", "Unknown") for r in records]
    counts = Counter(job_types)
    labels, values = zip(*counts.items())

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return f"data:image/png;base64,{encoded}"


def create_technician_bar_chart(records):
    """
    יוצר תרשים עמודות המציג את מספר השירותים לכל טכנאי ומחזיר אותו כ־PNG מקודד ב־Base64.

    Args:
        records (list[dict] | pd.DataFrame): רשימת רשומות שירות (כל רשומה מכילה שדה 'technician'),
                                             או DataFrame עם עמודת 'technician'.

    Returns:
        str: מחרוזת Base64 של תמונת ה־PNG המכילה את תרשים העמודות.

    Raises:
        ValueError: אם אין נתונים בתתי עמודת 'technician'.
        RuntimeError: אם אירעה שגיאה במהלך יצירת התרשים.
    """
    try:
        # המרת רשימת dict ל־DataFrame במידת הצורך
        if isinstance(records, list):
            df = pd.DataFrame(records)
        elif isinstance(records, pd.DataFrame):
            df = records.copy()
        else:
            raise ValueError("הפורמט של 'records' אינו נתמך. יש לספק רשימת dict או DataFrame.")

        # בדיקה שהעמודה 'tech' קיימת ומלאה
        if 'tech' not in df.columns or df['tech'].isna().all():
            raise ValueError("אין נתוני טכנאי לעיבוד בדוח.")

        # ספירת מספר השירותים לכל טכנאי
        technician_counts = df['tech'].value_counts().sort_values(ascending=False)

        # הגדרת גודל ופונטים לתרשים נגיש וברור
        plt.figure(figsize=(10, 6), dpi=100)
        ax = technician_counts.plot(
            kind='bar',
            edgecolor='black'
        )
        ax.set_title('Number of Jobs per Technician', fontsize=14, pad=12)
        ax.set_xlabel('Technician', fontsize=12)
        ax.set_ylabel('Number of Jobs', fontsize=12)
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()

        # שמירת התרשים לזיכרון כ־PNG והמרה ל־Base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()

        return f"data:image/png;base64,{chart_base64}"

    except ValueError as ve:
        logging.error(f"❌ create_technician_bar_chart: נתוני טכנאי לא תקינים - {ve}")
        raise
    except Exception as e:
        logging.error(f"❌ create_technician_bar_chart: שגיאה ביצירת תרשים העמודות - {e}", exc_info=True)
        raise RuntimeError("אירעה שגיאה ביצירת תרשים העמודות של הטכנאים.") from e


def get_jobs_by_date(date_str: str):
    """
    מחזיר רשימת עבודות (jobs) עבור תאריך מסוים (YYYY-MM-DD) מתוך קובץ אקסל/CSV בתיקיית output/<date_str>.
    אם אין קובץ מתאים – מחזיר רשימה ריקה.
    """
    import os
    import pandas as pd
    from pathlib import Path
    # חפש קובץ אקסל/CSV בתיקיית output/<date_str>
    base_dir = Path("output") / date_str
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    # חפש קובץ אקסל/CSV ראשון
    for file in base_dir.iterdir():
        if file.suffix.lower() in {".xlsx", ".csv"}:
            try:
                if file.suffix.lower() == ".xlsx":
                    df = pd.read_excel(file)
                else:
                    df = pd.read_csv(file)
                # המרה לרשימת dict
                jobs = df.to_dict(orient="records")
                return jobs
            except Exception as e:
                logging.error(f"get_jobs_by_date: Failed to read {file}: {e}")
                return []
    return []
