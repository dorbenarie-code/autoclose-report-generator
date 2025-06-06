# services/email_service.py

import os
import logging
from utils.mail_utils import send_email_with_attachments
from typing import Optional


class EmailService:
    """
    This class handles sending monthly report emails.
    It chooses the right recipient, builds subject and body,
    and attaches the PDF file.
    """

    def __init__(self, default_recipient: str = "manager@example.com"):
        # Remove extra spaces from default recipient email
        self.default_recipient = default_recipient.strip()

    def send_monthly_report(
        self,
        pdf_path: str,
        start_date: str,
        end_date: str,
        recipient: Optional[str] = None,
    ) -> bool:
        """
        Send the monthly PDF report by email.
        Args:
            pdf_path (str): Full path to the PDF file to send.
            start_date (str): Start date of the report (e.g., '2025-05-01').
            end_date (str): End date of the report (e.g., '2025-05-31').
            recipient (str): Optional custom email address. If missing, use default.
        Returns:
            bool: True if email was sent, False otherwise.
        """
        try:
            # Check that pdf_path is a non-empty string
            if not pdf_path or not isinstance(pdf_path, str):
                logging.error("❌ Invalid pdf_path provided.")
                return False

            # Check that the file exists and is not a directory
            if not os.path.isfile(pdf_path):
                logging.error(f"❌ PDF file not found or not a file: {pdf_path}")
                return False

            # Decide which email to send to: custom or default
            to_email = (recipient or self.default_recipient).strip()
            # Basic check for email format
            if "@" not in to_email or "." not in to_email:
                logging.error(f"❌ Invalid email address: {to_email}")
                return False

            # Build email subject and body
            subject = f"AutoClose Monthly Report: {start_date} to {end_date}"
            body = (
                "Hello,\n\n"
                f"Attached is the AutoClose monthly report from {start_date} to {end_date}.\n\n"
                "Best regards,\n"
                "AutoClose System"
            )

            logging.debug(
                f"Preparing to send email to {to_email} with attachment {pdf_path}"
            )
            success = send_email_with_attachments(
                to_address=to_email, subject=subject, body=body, attachments=[pdf_path]
            )

            if success:
                logging.info(f"✅ Monthly report sent to {to_email}")
            else:
                logging.error(f"❌ Failed to send report to {to_email}")
            return success

        except Exception:
            logging.exception("❌ Exception occurred while sending email")
            return False
