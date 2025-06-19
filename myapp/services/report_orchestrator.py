from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from myapp.etl.build_report_data import build_report_data
from myapp.services.pdf_export_service import PDFReportExporter
from myapp.services.email_service import EmailService
from myapp.utils.logger_config import get_logger
from myapp.services.report_analyzer import get_tech_summary
from myapp.config_shortcuts import EXPORT_DIR

log = get_logger(__name__)

# Default email recipients if none are provided
DEFAULT_EMAIL_TO = ["manager@yourcompany.com"]


def run_full_report_flow(
    excel_path: str,
    report_title: str = "Technician Job Report",
    send_email: bool = True,
    email_to: Optional[list[str]] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    tech_filter: Optional[list[str]] = None,
    service_filter: Optional[list[str]] = None,
    summary_only: bool = False,
) -> str:
    """
    Orchestrate the full report flow:
        1. Load and process job data from Excel
        2. Generate PDF report
        3. Optionally send email with report attached
        4. Return the full path to the generated PDF file
    """
    try:
        excel_file = Path(excel_path)
        if not excel_file.is_file():
            log.error("Input file not found: %s", excel_path)
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        # Ensure the export directory exists
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

        log.info(
            "Starting report flow | Excel: %s | Title: %s", excel_path, report_title
        )

        # Step 1: Process report data
        if summary_only:
            breakdown = get_tech_summary(
                str(excel_file),
                date_from=date_from,
                date_to=date_to,
                tech_filter=tech_filter,
                service_filter=service_filter,
            )
        else:
            df, summary = build_report_data(
                str(excel_file),
                date_from=date_from,
                date_to=date_to,
                tech_filter=tech_filter,
                service_filter=service_filter,
            )
            row_count = len(df)
            log.info("Processed data rows: %d", row_count)

            if row_count == 0:
                log.warning("No data available. Generating empty report.")

        # Step 2: Generate PDF
        unique_id = uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_title = report_title.replace(" ", "_")
        output_filename = f"{safe_title}_{unique_id}_{timestamp}.pdf"
        exporter = PDFReportExporter(df, title=report_title, export_dir=EXPORT_DIR)
        generated_path = exporter.export(filename=output_filename)
        log.info("PDF generated: %s", generated_path)

        # Step 3: Send email if requested
        if send_email:
            recipients = email_to or DEFAULT_EMAIL_TO
            email_service = EmailService()
            subject = f"[AutoClose] Report: {report_title}"
            body = (
                f"Please find attached the '{report_title}' report "
                f"generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
                f"Report ID: {output_filename}"
            )
            email_service.send_monthly_report(
                to=recipients[0],
                subject=subject,
                body=body,
                pdf_path=Path(generated_path),
                start_date=str(date_from),
                end_date=str(date_to),
            )
            log.info("Email sent to %s", recipients)

        log.info("Report flow completed successfully | Report ID: %s", output_filename)
        return str(generated_path)

    except Exception as e:
        log.exception("Report flow failed: %s", e)
        raise
