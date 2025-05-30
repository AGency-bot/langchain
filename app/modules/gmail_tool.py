import logging

from pydantic import BaseModel, Field
from langchain.tools import Tool

from app.utils.email_sender import send_email

# Konfiguracja loggera\logger = logging.getLogger(__name__)

class GmailInput(BaseModel):
    """
    Model wejściowy: temat i treść wiadomości e-mail.
    """
    subject: str = Field(..., description="Temat wiadomości e-mail, np. ID zlecenia")
    body: str = Field(..., description="Treść wiadomości e-mail, np. prośba o zlecenie")


def _send_email(tool_input: GmailInput) -> str:
    """
    Wysyła wiadomość e-mail poprzez moduł email_sender.
    Zwraca:
      - tekst potwierdzenia działania lub
      - komunikat o błędzie z prefiksem '❌'.
    """
    try:
        result = send_email(subject=tool_input.subject, body=tool_input.body)
        logging.info("✅ E-mail wysłany: %s", tool_input.subject)
        return result
    except Exception as e:
        error_msg = f"❌ Błąd wysyłki e-maila: {e}"
        logging.error(error_msg, exc_info=True)
        return error_msg

# Rejestracja narzędzia LangChain z funkcją zwracającą czysty string
gmail_tool = Tool.from_function(
    name="gmail_tool",
    description="Wysyła e-mail do giełdy z ID zlecenia i prośbą o jego pozyskanie.",
    func=_send_email,
    args_schema=GmailInput,
    return_direct=True
)
