import os
import time
import logging
import requests

from pydantic import BaseModel
from langchain_core.tools import StructuredTool

from app.modules.fetch_status_tool import check_fetch_status, FetchStatusInput
from app.modules.fetch_restart_tool import restart_fetch, FetchRestartInput
from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# Bazowy URL do usługi Fetch
_default_url = "https://fetch-2-0-service.onrender.com"
_FETCH_BASE_URL = os.getenv("FETCH_BASE_URL")
if not _FETCH_BASE_URL:
    logger.warning("FETCH_BASE_URL nie ustawione, używam domyślnego: %s", _default_url)
FETCH_BASE_URL = _FETCH_BASE_URL or _default_url

class EmptyInput(BaseModel):
    """
    Brak argumentów wejściowych dla narzędzia Fetch.
    """
    pass

class FetchResponse(BaseModel):
    success: bool
    message: str
    source: str  # 'status', 'restart', 'start', 'exception'


def _start_fetch(tool_input: EmptyInput) -> str:
    """
    Zarządza uruchomieniem usługi Fetch:
    - sprawdza status
    - restartuje, jeśli jest offline lub uszkodzony
    - wywołuje endpoint /start
    """
    try:
        # Sprawdzenie statusu Fetch
        status = check_fetch_status.run(tool_input=FetchStatusInput())
        logger.info("Status Fetch: %s", status)

        # Restart, jeśli nie działa
        if not status or any(k in status.lower() for k in ("błąd", "offline")):
            logger.warning("Fetch nie działa – próbuję restart...")
            restart_resp = restart_fetch.run(tool_input=FetchRestartInput()) or ""
            logger.info("Wynik restartu: %s", restart_resp)

            if not restart_resp.startswith("✅"):
                return FetchResponse(
                    success=False,
                    message=restart_resp,
                    source="restart"
                ).json()

            # Oczekiwanie na powrót online
            for attempt in range(5):
                time.sleep(2)
                check = check_fetch_status.run(tool_input=FetchStatusInput())
                logger.info("Próba %d: %s", attempt + 1, check)
                if check and "online" in check.lower():
                    break
            else:
                return FetchResponse(
                    success=False,
                    message="Po restarcie Fetch nie wstał prawidłowo.",
                    source="status"
                ).json()

        # Uruchomienie /start
        logger.info("Uruchamiam Fetch poprzez %s/start", FETCH_BASE_URL)
        resp = requests.get(f"{FETCH_BASE_URL}/start", timeout=10)
        resp.raise_for_status()

        return FetchResponse(
            success=True,
            message=f"Fetch uruchomiony. Odpowiedź: {resp.text}",
            source="start"
        ).json()

    except Exception as e:
        # Raport błędu i log
        report_error("FetchTool", "start_fetch", e)
        logger.error("Błąd podczas uruchamiania Fetch: %s", e, exc_info=True)
        return FetchResponse(
            success=False,
            message=f"Błąd uruchamiania Fetch: {e}",
            source="exception"
        ).json()

# Definicja narzędzia LangChain
start_fetch = StructuredTool.from_function(
    name="start_fetch",
    description=(
        "Zarządza uruchomieniem Fetch: sprawdza status, restartuje jeśli trzeba, "
        "i wywołuje endpoint /start."
    ),
    func=_start_fetch,
    args_schema=EmptyInput
)
