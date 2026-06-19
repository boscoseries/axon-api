import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)


def send_error_email(subject: str, body: str) -> None:
    """
    Send an error alert email via SMTP STARTTLS (port 587).
    Called automatically by SESHandler on logger.error() or logger.critical().
    """

    admin_emails = settings.admin_emails.split(",")[0]
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Axon API Error] - {subject}"
        msg["From"] = settings.smtp_from
        msg["To"] = admin_emails  # support multiple recipients via comma-separated string in .env

        # Plain text version
        text_part = MIMEText(body, "plain")

        # HTML version — slightly nicer in email clients
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #dc2626;">Axon API — Error Alert</h2>
            <pre style="background:#f3f4f6; padding:16px; border-radius:6px; font-size:13px;">{body}</pre>
          </body>
        </html>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, admin_emails, msg.as_string())

    except Exception as e:
        # Never let the notifier crash the app — just print to stdout
        logger.warning(f"[notifier] Failed to send error email: {e}")


def send_notification_email(subject: str, body: str) -> None:
    """
    Send a plain notification email (not an error alert).
    Subject prefix is [Axon API] instead of [Axon API Error].
    """
    admin_emails = settings.admin_emails.split(",")[0]
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Axon API] {subject}"
        msg["From"] = settings.smtp_from
        msg["To"] = admin_emails

        text_part = MIMEText(body, "plain")
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">Axon API — Notification</h2>
            <pre style="background:#f3f4f6; padding:16px; border-radius:6px; font-size:13px;">{body}</pre>
          </body>
        </html>
        """
        html_part = MIMEText(html_body, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, admin_emails, msg.as_string())

    except Exception as e:
        logger.warning(f"[notifier] Failed to send notification email: {e}")


class SMTPErrorHandler(logging.Handler):
    """
    Attaches to the root logger.
    Any logger.error() or logger.critical() anywhere in the codebase
    automatically triggers an email — no changes needed to existing log calls.
    """
    def __init__(self):
        super().__init__(level=logging.ERROR)  # Only trigger on ERROR or CRITICAL

    def emit(self, record: logging.LogRecord) -> None:
        # Skip if the record came from notifier itself — breaks the loop
        if record.name == __name__:
            return

        subject = f"{record.levelname} in {record.module}: {record.getMessage()[:50]}"
        # Include full traceback if an exception was attached
        if record.exc_info:
            tb = traceback.format_exception(*record.exc_info)
            body = f"{record.getMessage()}\n\n{''.join(tb)}"
        else:
            body = (
                f"Level:    {record.levelname}\n"
                f"Logger:   {record.name}\n"
                f"Module:   {record.module}\n"
                f"Function: {record.funcName}\n"
                f"Line:     {record.lineno}\n\n"
                f"Message:\n{record.getMessage()}"
            )

        send_error_email(subject=subject, body=body)