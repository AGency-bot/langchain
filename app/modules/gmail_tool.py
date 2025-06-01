# app/modules/gmail_tool.py

import os
import logging
from typing import Dict

from langchain_core.tools import Tool
from pydantic import BaseModel, ValidationError

from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)

class GmailInput(BaseModel):
    subject: str
    body: str

def send_gmail_email(data: Dict[str, str]) -> str:
    """
    Wysyła e-mail z podanym tematem i treścią.
    Wymaga ENV: GMAIL_USER, GMAIL_PASSWORD.
    :param data: dict z polami 'subject' i 'body'
    :return: komunikat o sukcesie lub błędzie
    """
    try:
        parsed = GmailInput.parse_obj(data)
        from_address = os.getenv("GMAIL_USER")
        password = os.getenv("GMAIL_PASSWORD")
        to_address = os.getenv("GMAIL_RECIPIENT", from_address)

        if not from_address or not password:
            return "❌ Brakuje konfiguracji GMAIL_USER lub GMAIL_PASSWORD"

        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(parsed.body)
        msg["Subject"] = parsed.subject
        msg["From"] = from_address
        msg["To"] = to_address

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_address, password)
        server.sendmail(from_address, [to_address], msg.as_string())
        server.quit()

        success = f"✅ E-mail wysłany do {to_address}"
        logger.info(success)
        return success

    except ValidationError as ve:
        return f"❌ Błędne dane wejściowe: {ve}"
    except Exception as e:
        report_error("gmail_tool", "send_gmail_email", e)
        logger.error("❌ Błąd wysyłania e-maila: %s", e, exc_info=True)
        return f"❌ Błąd wysyłania e-maila: {e}"
    
gmail_tool = Tool.from_function(
    name="gmail_tool",
    description="Wysyła e-mail z podanym tematem i treścią. Wymaga skonfigurowanego GMAIL_USER.",
    func=send_gmail_email,
    args_schema=GmailInput, 
    return_direct=True
)