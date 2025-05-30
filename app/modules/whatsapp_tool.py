import os
import logging
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from langchain.tools import Tool

from app.utils.error_reporter import report_error

# Wczytaj zmienne środowiskowe z .env
load_dotenv()

# Konfiguracja loggera
logger = logging.getLogger(__name__)


def _send_whatsapp(content_variables: str) -> str:
    """
    Wysyła WhatsApp template message przez Twilio (Business-initiated).
    Fallback: jeśli szablon nieaktywny (sandbox), wysyła zwykły body.
    :param content_variables: JSON-string z placeholderami, np. '{"1":"12/1","2":"3pm"}'
    """
    try:
        # Odczyt konfiguracji z ENV
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")
        to_whatsapp = os.getenv("TWILIO_WHATSAPP_TO")
        content_sid = os.getenv("TWILIO_WHATSAPP_CONTENT_SID")

        missing = [
            var for var in [
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_WHATSAPP_FROM",
                "TWILIO_WHATSAPP_TO",
                "TWILIO_WHATSAPP_CONTENT_SID",
            ] if not os.getenv(var)
        ]
        if missing:
            msg = f"❌ Brakuje konfiguracji Twilio WhatsApp: {', '.join(missing)}"
            logger.error(msg)
            return msg

        client = Client(account_sid, auth_token)
        try:
            # Próba wysłania wiadomości szablonem
            message = client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                content_sid=content_sid,
                content_variables=content_variables,
            )
        except TwilioRestException as e:
            # Fallback: w sandboxie szablony mogą nie być aktywne (kod 21655)
            if e.code == 21655:
                logger.warning("🔄 Szablon nieaktywny, wysyłam fallback jako body.")
                message = client.messages.create(
                    from_=from_whatsapp,
                    to=to_whatsapp,
                    body=content_variables,
                )
            else:
                raise

        success = f"✅ Wiadomość WhatsApp wysłana. SID: {message.sid}"
        logger.info(success)
        return success

    except Exception as e:
        # Zgłoś błąd do debuggera i zloguj
        try:
            report_error("WhatsAppTool", "_send_whatsapp", e)
        except Exception:
            logger.warning("⚠️ Nie można zgłosić błędu do debuggera.")
        logger.error("❌ Błąd podczas wysyłania wiadomości WhatsApp: %s", e, exc_info=True)
        return f"❌ Błąd podczas wysyłania wiadomości WhatsApp: {e}"


# Rejestracja narzędzia LangChain jako prostej funkcji przyjmującej string
whatsapp_template_tool = Tool.from_function(
    name="whatsapp_template_tool",
    description=(
        "Wysyła WhatsApp template message przez Twilio (Business-initiated). "
        "Jeśli szablon nieaktywny (sandbox), używa fallback body."
    ),
    func=_send_whatsapp,
    return_direct=True
)