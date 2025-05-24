import logging

from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.utils.email_sender import send_email

# Konfiguracja loggera
logger = logging.getLogger(__name__)

class GmailInput(BaseModel):
    """
    Model wejściowy: temat i treść wiadomości e-mail.
    """
    subject: str = Field(..., description="Temat wiadomości e-mail (np. ID zlecenia)")
    body: str = Field(..., description="Treść wiadomości e-mail (np. Proszę o zlecenie ...)")


def _send_email(tool_input: GmailInput) -> str:
    """
    Wysyła wiadomość e-mail poprzez email_sender.
    Zwraca komunikat zwrotny lub błąd z prefiksem '❌'.
    """
    try:
        result = send_email(subject=tool_input.subject, body=tool_input.body)
        logger.info("Wysłano e-mail: %s", tool_input.subject)
        return result
    except Exception as e:
        report = f"❌ Błąd wysyłki e-maila: {e}"
        logger.error(report, exc_info=True)
        return report

# Rejestracja narzędzia LangChain
gmail_tool = Tool.from_function(
    name="gmail_tool",
    description="Wysyła e-mail do giełdy z ID zlecenia i prośbą o jego pozyskanie",
    func=_send_email,
    args_schema=GmailInput
)
