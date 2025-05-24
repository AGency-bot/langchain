import os
import logging

from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from twilio.rest import Client
from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

class WhatsAppInput(BaseModel):
    """
    Model wejściowy: treść wiadomości WhatsApp.
    """
    message: str = Field(..., description="Treść wiadomości WhatsApp do wysłania")


def _send_whatsapp(tool_input: WhatsAppInput) -> str:
    """
    Wysyła wiadomość WhatsApp przy użyciu Twilio.
    Zwraca komunikat o sukcesie lub błąd z prefiksem '❌'.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")
        to_whatsapp = os.getenv("TWILIO_WHATSAPP_TO")

        missing = [var for var in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_TO") if not os.getenv(var)]
        if missing:
            msg = f"❌ Brakuje konfiguracji Twilio WhatsApp: {', '.join(missing)}"
            logger.error(msg)
            return msg

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_whatsapp,
            to=to_whatsapp,
            body=tool_input.message
        )
        success = f"✅ Wiadomość WhatsApp wysłana. SID: {message.sid}"
        logger.info(success)
        return success

    except Exception as e:
        report_error("WhatsAppTool", "_send_whatsapp", e)
        logger.error("❌ Błąd podczas wysyłania wiadomości WhatsApp: %s", e, exc_info=True)
        return f"❌ Błąd podczas wysyłania wiadomości WhatsApp: {e}"

# Rejestracja narzędzia LangChain
whatsapp_tool = Tool.from_function(
    name="whatsapp_tool",
    description="Wysyła wiadomość WhatsApp przez Twilio.",
    func=_send_whatsapp,
    args_schema=WhatsAppInput
)
