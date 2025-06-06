# routes/history_reports.py

import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import csv
import io
from flask import Blueprint, render_template, request, Response

history_bp = Blueprint("history_reports", __name__)

# הגדרת תיקיות הדוחות הקיימות
REPORT_DIRS = {
    "Client Report": Path("static/client_reports"),
    "Monthly Summary": Path("static/monthly_reports"),
}


@history_bp.route("/reports/history")
def report_history() -> str:
    """
    מציג את היסטוריית הדוחות ונותן אפשרות לסנן לפי טווח תאריכים ושם טכנאי.
    """
    report_files = []

    # קריאת פרמטרי הסינון מה-URL
    start_str = request.args.get("start", "").strip()
    end_str = request.args.get("end", "").strip()
    tech_filter = request.args.get("tech", "").strip().lower()
    type_filter = request.args.get("type", "").strip()
    search_filter = request.args.get("search", "").strip().lower()

    # המרת מחרוזות תאריכים לאובייקטי date (אם זמינים)
    start_date = None
    end_date = None
    try:
        if start_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    except ValueError:
        logging.warning(f"Invalid start date format: {start_str}")
    try:
        if end_str:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        logging.warning(f"Invalid end date format: {end_str}")

    for report_type, folder_path in REPORT_DIRS.items():
        # אם התיקייה לא קיימת או אינה תיקייה, מדלגים
        if not folder_path.exists() or not folder_path.is_dir():
            continue

        for entry in folder_path.iterdir():
            if not entry.is_file():
                continue

            # קבלת תאריך יצירת הקובץ
            try:
                created_dt = datetime.fromtimestamp(entry.stat().st_ctime)
                created_date = created_dt.date()
                created_str = created_dt.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                logging.error(
                    f"Error getting creation time for {entry}: {e}", exc_info=True
                )
                created_str = "Unknown"
                created_date = None

            # סינון לפי טווח תאריכים
            if start_date and created_date:
                if created_date < start_date:
                    continue
            if end_date and created_date:
                if created_date > end_date:
                    continue

            # סינון לפי טכנאי (מבוסס שם קובץ, lower-case)
            if tech_filter and tech_filter not in entry.name.lower():
                continue

            # סינון לפי סוג דוח
            if type_filter and report_type != type_filter:
                continue

            # סינון חופשי (שם קובץ, סוג, תאריך)
            if search_filter:
                search_target = f"{entry.name} {report_type} {created_str}".lower()
                if search_filter not in search_target:
                    continue

            report_files.append(
                {
                    "name": entry.name,
                    "type": report_type,
                    "date": created_str,
                    "path": f"{folder_path.name}/{entry.name}",
                }
            )

    # מיון לפי תאריך יצירה בסדר יורד (Unknown יבוא בסוף)
    report_files.sort(
        key=lambda r: r["date"] if r["date"] != "Unknown" else "", reverse=True
    )

    # קיבוץ לפי תאריך (YYYY-MM-DD) עבור גרף
    chart_data: dict[str, int] = defaultdict(int)
    for file in report_files:
        date_key = file["date"][:10]  # חותך YYYY-MM-DD
        chart_data[date_key] += 1
    chart_labels = sorted(chart_data.keys())
    chart_values = [chart_data[date] for date in chart_labels]

    return render_template(
        "reports/report_history.html",
        report_files=report_files,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@history_bp.route("/reports/history/export")
def export_report_history() -> Response:
    """
    Exports the entire report history as a CSV file.
    כותרות העמודות: Filename, Type, Date Created, Relative Path.
    """
    # יצירת אובייקט StringIO לשמירת ה-CSV בזיכרון
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Filename", "Type", "Date Created", "Relative Path"])

    # בנייה פשוטה כמו בלוגיקה המקורית: קריאה לתיקיות והוספת כל הקבצים
    for report_type, folder_path in REPORT_DIRS.items():
        if not folder_path.exists() or not folder_path.is_dir():
            logging.debug(f"Folder not found or not a directory: {folder_path}")
            continue

        for entry in folder_path.iterdir():
            if not entry.is_file():
                continue
            try:
                created_dt = datetime.fromtimestamp(entry.stat().st_ctime)
                created_str = created_dt.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                logging.error(
                    f"Error getting creation time for {entry}: {e}", exc_info=True
                )
                created_str = "Unknown"

            relative_path = f"{folder_path.name}/{entry.name}"
            writer.writerow([entry.name, report_type, created_str, relative_path])

    # בניית התגובה עם תוכן ה-CSV
    csv_content = output.getvalue()
    output.close()

    response = Response(csv_content, mimetype="text/csv; charset=utf-8")
    response.headers.set(
        "Content-Disposition", "attachment", filename="report_history_export.csv"
    )
    return response
