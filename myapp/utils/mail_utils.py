# services/mail_utils.py

import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)


def send_report_email(report_path: str) -> bool:
    """
    Sends the generated report via email with a PDF attachment.

    Steps:
      1. Load environment variables (sender, receiver, password, etc.).
      2. Build an email message (subject, body, attachments).
      3. Connect securely to an SMTP server.
      4. Send the email and log the result.
      5. Returns True if the email is sent successfully.
         Raises an exception on failure.
    """
    # 1. Load environment variables
    email_sender = os.environ.get("EMAIL_SENDER")
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_receiver = os.environ.get("EMAIL_RECEIVER")
    bcc = os.environ.get("EMAIL_BCC", "")

    # Subject & body with default fallbacks
    email_subject = os.environ.get("EMAIL_SUBJECT", "AutoClose Report - ${FILENAME}")
    # Hebrew fallback if EMAIL_BODY is not defined
    email_body = (
        os.environ.get("EMAIL_BODY")
        or f"הדוח ליום {datetime.now().strftime('%Y-%m-%d')} מצורף בקובץ PDF. תודה, צוות AutoClose."
    )

    # Validate required variables
    if not (email_sender and email_password and email_receiver):
        msg = (
            "Missing one or more required environment variables "
            "(EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER)."
        )
        logger.error(msg)
        raise EnvironmentError(msg)

    # 2. Prepare placeholders
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.basename(report_path)

    # Replace placeholders in subject and body
    # Example: ${FILENAME} , ${DATE}
    email_subject = email_subject.replace("${FILENAME}", filename).replace(
        "${DATE}", current_date_str
    )
    email_body = email_body.replace("${FILENAME}", filename).replace(
        "${DATE}", current_date_str
    )

    # 3. Build the MIMEMultipart message
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = email_receiver
    message["Subject"] = email_subject

    if bcc:
        message["Bcc"] = bcc

    # Attach plain text body
    message.attach(MIMEText(email_body, "plain"))

    # Attach PDF
    try:
        with open(report_path, "rb") as pdf_file:
            pdf_attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
            pdf_attachment.add_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            message.attach(pdf_attachment)
    except FileNotFoundError as e:
        logger.error(f"PDF file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading the PDF file: {e}")
        raise

    # 4. Send the email via SMTP (SSL) - example using Gmail
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_sender, email_password)
            smtp.send_message(message)
            logger.info(
                f"Email sent successfully to {email_receiver}. "
                f"BCC: {bcc if bcc else 'None'}"
            )
            return True
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        raise
