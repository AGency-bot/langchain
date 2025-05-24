import os
import smtplib
import logging
from email.message import EmailMessage
from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)

def send_email(subject: str, body: str) -> str:
    """
    Wysyła wiadomość e-mail za pomocą danych z konfiguracji środowiskowej.
    """
    try:
        sender = os.getenv("GMAIL_ADDRESS")
        password = os.getenv("GMAIL_PASSWORD")
        receiver = os.getenv("GMAIL_RECEIVER")

        if not all([sender, password, receiver]):
            return "❌ Brakuje danych konfiguracyjnych dla Gmaila (GMAIL_ADDRESS, GMAIL_PASSWORD, GMAIL_RECEIVER)"

        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

        logger.info(f"✅ E-mail wysłany do {receiver} z tematem '{subject}'")
        return "✅ E-mail wysłany pomyślnie"

    except Exception as e:
        report_error("EmailSender", "send_email", e)
        logger.error(f"❌ Błąd podczas wysyłania e-maila: {e}")
        return f"❌ Błąd podczas wysyłania e-maila: {str(e)}"
