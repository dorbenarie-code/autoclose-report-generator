import pandas as pd
import os
from datetime import datetime
import logging
import plotly.express as px
from pathlib import Path

from myapp.services.pdf_export_service import PDFReportExporter
from myapp.services.email_service import EmailService

# Configure a basic logger that writes to 'output/auto_run.log'
LOG_FILE_PATH = "output/auto_run.log"
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

DATA_FILE = "output/merged_jobs.csv"
EXPORT_DIR = "output/reports_exported"


def auto_run() -> None:
    """
    Automates the process of:
      1. Checking if 'merged_jobs.csv' exists and loading the data.
      2. Generating a PDF report from the data.
      3. Sending the report via email using EmailService.
      4. Logging each step and any errors to 'auto_run.log'.
    """
    try:
        # 1. Validate data file existence
        if not os.path.isfile(DATA_FILE):
            msg = f"❌ Data file not found: {DATA_FILE}"
            logging.warning(msg)
            print(msg)
            return

        df = pd.read_csv(DATA_FILE)

        if df.empty:
            logging.info("⚠️ No data to export in %s.", DATA_FILE)
            return

        # 2. Create PDF
        logging.info("📄 Exporting PDF report...")
        exporter = PDFReportExporter(df)
        filename = exporter.export()

        pdf_path = os.path.join(EXPORT_DIR, filename)
        if not os.path.isfile(pdf_path):
            logging.warning("❌ PDF report did not get created: %s", pdf_path)
            return

        # 3. Prepare email date range
        start_date = "2025-06-01"
        end_date = datetime.today().strftime("%Y-%m-%d")

        # 4. Send via Email
        logging.info("📧 Sending report via email...")
        mailer = EmailService()

        # Use a default recipient email since recipient_email is not defined
        recipient = "manager@yourcompany.com"
        mailer.send_monthly_report(
            to=recipient,
            subject="Monthly Report",
            body="Attached is your monthly report.",
            pdf_path=Path(pdf_path),
            start_date=str(start_date),
            end_date=str(end_date)
        )

    except Exception as e:
        # Logs the full traceback in 'auto_run.log'
        logging.exception("🔥 Auto-run process failed: %s", e)


if __name__ == "__main__":
    auto_run()
