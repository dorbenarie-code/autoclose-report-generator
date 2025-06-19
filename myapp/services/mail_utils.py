import os
import logging
from typing import Optional, List
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from myapp.utils.logger_config import get_logger

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
log = get_logger(__name__)


def send_report_by_email(
    to_email: str,
    subject: str,
    body: str,
    attachment_paths: Optional[list[str]] = None,
    html: bool = False,
) -> bool:
    """
    Sends an email with optional attachments using SMTP.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, to_email]):
        log.error("❌ Missing email config in .env")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    if html:
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    if attachment_paths:
        for file_path in attachment_paths:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                log.error(f"⚠ Attachment missing or empty: {file_path}")
                return False
            with open(file_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(file_path),
                )

    try:
        sender = EMAIL_SENDER or ""
        password = EMAIL_PASSWORD or ""
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        log.info(f"✅ Email sent successfully to {to_email}.")
        return True
    except Exception as e:
        log.error(f"🔥 Failed to send email: {e}", exc_info=True)
        return False
