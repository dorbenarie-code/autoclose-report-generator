# utils/mail_utils.py

import os
import logging
import smtplib
import yagmail
from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import date

# Load environment variables
load_dotenv()

# Retrieve email configuration from environment
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_SUBJECT_TEMPLATE = os.getenv("EMAIL_SUBJECT", "AutoClose Report – ${DATE}")
EMAIL_BODY_TEMPLATE = os.getenv(
    "EMAIL_BODY", "Attached is your AutoClose report. Please review."
)

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [MAIL_UTILS] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_email_with_attachments(
    to_address: str, subject: str, body: str, attachments: list[str]
) -> bool:
    """
    Send an email with the specified attachments via Gmail SMTP.
    Args:
        to_address (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body.
        attachments (list[str]): List of file paths to attach.
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    # Validate environment variables
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, to_address]):
        error_msg = "Missing email configuration in .env or to_address"
        logger.error(error_msg)
        return False

    # Initialize the email message
    msg: EmailMessage = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER if EMAIL_SENDER is not None else ""
    msg["To"] = to_address if to_address is not None else ""
    msg.set_content(body)

    # Attach files
    for file_path in attachments:
        path = Path(file_path)
        if not path.is_file():
            msg_err = f"Attachment not found: {file_path}"
            logger.error(msg_err)
            return False
        logger.info(f"Attaching file: {path.name}")
        with path.open("rb") as f:
            file_data = f.read()
            msg.add_attachment(
                file_data,
                maintype="application",
                subtype="octet-stream",
                filename=path.name,
            )

    # Send email via Gmail SMTP over SSL
    try:
        logger.info(f"Connecting to SMTP server as {EMAIL_SENDER}")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER or "", EMAIL_PASSWORD or "")
            smtp.send_message(msg)
        logger.info(
            f"Email sent successfully to {to_address} with {len(attachments)} attachment(s)."
        )
        return True
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_email_with_attachment(
    recipient: str, subject: str, body: str, attachment_path: str
) -> None:
    """
    Sends an email with a PDF (or any file) attachment using SMTP via yagmail.

    Args:
        recipient (str):   Recipient email address.
        subject (str):     Subject of the email.
        body (str):        Body text of the email.
        attachment_path (str): Full filesystem path to the file to attach.

    Raises:
        RuntimeError: If any required environment variable is missing or sending fails.
    """
    # Validate environment variables
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender or not password:
        logging.error("EMAIL_SENDER or EMAIL_PASSWORD not set in environment.")
        raise RuntimeError(
            "Missing EMAIL_SENDER or EMAIL_PASSWORD environment variables."
        )

    # Validate function arguments
    if not recipient:
        logging.error("Recipient email address is empty.")
        raise ValueError("Recipient email address must be provided.")
    if not subject:
        logging.error("Email subject is empty.")
        raise ValueError("Email subject must be provided.")
    if not os.path.isfile(attachment_path):
        logging.error(f"Attachment file not found at path: {attachment_path}")
        raise FileNotFoundError(f"Attachment not found: {attachment_path}")

    try:
        # Initialize SMTP client
        yag = yagmail.SMTP(user=sender, password=password)

        # Prepare email contents: body text and attachment
        contents = [body, attachment_path]

        logging.info(
            f"Sending email to {recipient} with subject '{subject}' and attachment "
            f"'{attachment_path}'"
        )
        yag.send(to=recipient, subject=subject, contents=contents)
        logging.info(f"✅ Email sent successfully to {recipient}")

    except Exception as e:
        logging.error(f"❌ Failed to send email to {recipient}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to send email: {e}") from e


def send_monthly_report(output_path: str) -> None:
    """
    Sends the monthly summary report PDF via email using credentials and templates from .env.

    Args:
        output_path (str): Full path to the PDF file to be attached.
    """
    try:
        sender = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        receiver = os.getenv("EMAIL_RECEIVER")

        today = date.today().isoformat()
        subject = os.getenv("EMAIL_SUBJECT", "AutoClose Report").replace(
            "${DATE}", today
        )
        body = (
            os.getenv("EMAIL_BODY", "").replace("${DATE}", today).replace("\\n", "\n")
        )

        yag = yagmail.SMTP(user=sender, password=password)
        yag.send(to=receiver, subject=subject, contents=[body, output_path])

        print(f"✅ Email sent to {receiver} with report: {output_path}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise
