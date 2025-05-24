import os
import time
import logging
import requests

from pydantic import BaseModel
from langchain_core.tools import StructuredTool

from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# Bazowy URL do usługi Fetch
_default_url = "https://fetch-2-0-service.onrender.com"
_FETCH_BASE_URL = os.getenv("FETCH_BASE_URL")
if not _FETCH_BASE_URL:
    logger.warning("FETCH_BASE_URL nie ustawione, używam domyślnego: %s", _default_url)
FETCH_BASE_URL = _FETCH_BASE_URL or _default_url

class FetchRestartInput(BaseModel):
    """
    Brak danych wejściowych dla restartu Fetch.
    """
    pass


def _restart_fetch(tool_input: FetchRestartInput) -> str:
    """
    Restartuje usługę Fetch:
      1. Wywołuje endpoint /stop
      2. Czeka 2 sekundy
      3. Wywołuje endpoint /start
      4. Sprawdza status przez /status (max 5 prób)
    Zwraca komunikat o wyniku operacji.
    """
    try:
        logger.info("⏹️ Próbuję zatrzymać Fetch...")
        stop_resp = requests.get(f"{FETCH_BASE_URL}/stop", timeout=10)
        stop_resp.raise_for_status()

        logger.info("⏳ Czekam 2s na wyłączenie...")
        time.sleep(2)

        logger.info("▶️ Uruchamiam Fetch ponownie...")
        start_resp = requests.get(f"{FETCH_BASE_URL}/start", timeout=10)
        start_resp.raise_for_status()

        # Sprawdzenie statusu Fetch
        for attempt in range(5):
            time.sleep(1)
            try:
                check_resp = requests.get(f"{FETCH_BASE_URL}/status", timeout=5)
                check_resp.raise_for_status()
                data = check_resp.json()
                if data.get("status") is True:
                    return "✅ Fetch został pomyślnie zrestartowany i działa"
            except Exception:
                logger.debug("Próba %d nieudana", attempt + 1)
                continue

        return "⚠️ Fetch zrestartowany, ale nie odpowiedział poprawnie na /status"

    except requests.RequestException as e:
        report_error("FetchRestartTool", "restart_fetch", e)
        logger.error("❌ Błąd HTTP przy restarcie Fetch: %s", e, exc_info=True)
        return f"❌ Błąd HTTP przy restarcie Fetch: {e}"

    except Exception as e:
        report_error("FetchRestartTool", "restart_fetch", e)
        logger.error("❌ Błąd ogólny podczas restartu Fetch: %s", e, exc_info=True)
        return f"❌ Błąd ogólny podczas restartu Fetch: {e}"

# Rejestracja narzędzia LangChain
restart_fetch = StructuredTool.from_function(
    name="restart_fetch",
    description="Restartuje aplikację Fetch przez endpointy /stop i /start.",
    func=_restart_fetch,
    args_schema=FetchRestartInput
)