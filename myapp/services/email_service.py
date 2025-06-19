from myapp.utils.logger_config import get_logger
from pathlib import Path
from typing import Optional

logger = get_logger(__name__)
# services/email_service.py

import os
import logging
from myapp.services.mail_utils import send_report_by_email
import csv
from datetime import datetime


class EmailService:
    """
    This class handles sending monthly report emails.
    It chooses the right recipient, builds subject and body,
    and attaches the PDF file.
    """

    def __init__(self, default_recipient: str = "dormahalal@gmail.com"):
        # Remove extra spaces from default recipient email
        self.default_recipient = default_recipient.strip()

    def _log_email_action(
        self, recipient: str, attachments: list[str], status: bool, error_msg: str = ""
    ) -> None:
        log_path = "output/sent_email_log.csv"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, mode="a", newline="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    recipient,
                    "; ".join(attachments),
                    "Success" if status else "Failed",
                    error_msg,
                ]
            )

    def send(
        self, to: str, subject: str, body: str, attachment: Optional[Path] = None
    ) -> None:
        pass

    def send_monthly_report(
        self,
        to: str,
        subject: str,
        body: str,
        pdf_path: Optional[Path] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> None:
        """
        Send the monthly PDF report by email.
        Args:
            pdf_path (Path | None): Full path to the PDF file to send.
            start_date (str | None): Start date of the report (e.g., '2025-05-01').
            end_date (str | None): End date of the report (e.g., '2025-05-31').
            to (str): Custom email address.
            subject (str): Email subject.
            body (str): Email body.
        Returns:
            None
        """
        error_msg = ""
        try:
            if pdf_path and not isinstance(pdf_path, Path):
                logging.error("❌ Invalid pdf_path provided.")
                error_msg = "Invalid pdf_path provided."
                self._log_email_action(to, [], False, error_msg)
                return

            if pdf_path and not os.path.isfile(pdf_path):
                logging.error(f"❌ PDF file not found or not a file: {pdf_path}")
                error_msg = f"PDF file not found: {pdf_path}"
                self._log_email_action(to, [str(pdf_path)], False, error_msg)
                return

            to_email = to.strip()
            if "@" not in to_email or "." not in to_email:
                logging.error(f"❌ Invalid email address: {to_email}")
                error_msg = f"Invalid email address: {to_email}"
                self._log_email_action(to_email, [], False, error_msg)
                return

            logging.debug(
                f"Preparing to send email to {to_email} with attachment {pdf_path}"
            )
            success = send_report_by_email(
                to_email=to_email,
                subject=subject,
                body=body,
                attachment_paths=[str(pdf_path)] if pdf_path else [],
            )

            if success:
                logging.info(f"✅ Monthly report sent to {to_email}")
                self._log_email_action(
                    to_email, [str(pdf_path)] if pdf_path else [], True, ""
                )
            else:
                logging.error(f"❌ Failed to send report to {to_email}")
                error_msg = f"Failed to send report to {to_email}"
                self._log_email_action(
                    to_email, [str(pdf_path)] if pdf_path else [], False, error_msg
                )
            return

        except Exception as e:
            logging.exception("❌ Exception occurred while sending email")
            self._log_email_action(to, [], False, str(e))
            return
