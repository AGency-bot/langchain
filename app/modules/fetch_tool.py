# app/modules/fetch_tool.py

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from langchain.tools import StructuredTool

from app.utils.fetch_api_client import FetchAPIClient
from app.modules.fetch_status_tool import check_fetch_status, FetchStatusInput
from app.modules.fetch_restart_tool import restart_fetch, FetchRestartInput
from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class EmptyInput(BaseModel):
    """Brak argumentów wejściowych."""
    pass

class FetchResponse(BaseModel):
    success: bool
    message: str
    source: str  # "status", "restart", "start", "exception"

def _start_fetch(tool_input: Optional[EmptyInput] = None) -> Dict[str, Any]:
    """
    Uruchamia Fetch:
    - sprawdza status,
    - restartuje jeśli usługa nie działa,
    - czeka na “running” po restarcie,
    - retryuje /start,
    - zwraca dict z kluczami: success, message, source.
    """
    try:
        client = FetchAPIClient()

        # 1. Sprawdzenie statusu
        status = check_fetch_status.run(tool_input=FetchStatusInput())
        logger.info("Status Fetch: %s", status)

        # 2. Restart w razie potrzeby
        if not status or status.startswith("❌"):
            logger.warning("Fetch nie działa – próbuję restart...")
            restart_resp = restart_fetch.run(tool_input=FetchRestartInput())
            logger.info("Wynik restartu: %s", restart_resp)
            if not restart_resp.startswith("✅"):
                return FetchResponse(success=False, message=restart_resp, source="restart").dict()

            # Dłuższe oczekiwanie na cold-start
            for i in range(10):
                status_after = check_fetch_status.run(tool_input=FetchStatusInput())
                logger.info("Sprawdzam status po restarcie (%d/10): %s", i+1, status_after)
                if status_after.startswith("✅"):
                    break

        # 3. Retry wywołania /start
        for attempt in range(3):
            logger.info("Uruchamiam Fetch (próba %d/3)", attempt+1)
            resp = client.start()
            if resp:
                return FetchResponse(
                    success=True,
                    message=f"Fetch uruchomiony: {resp}",
                    source="start"
                ).dict()
            logger.warning("Próba %d nieudana, ponawiam...", attempt+1)

        # 4. Po 3 nieudanych próbach
        return FetchResponse(
            success=False,
            message="❌ Nie udało się wywołać /start po 3 próbach",
            source="start"
        ).dict()

    except Exception as e:
        report_error("FetchTool", "start_fetch", e)
        logger.error("Błąd podczas uruchamiania Fetch: %s", e, exc_info=True)
        return FetchResponse(
            success=False,
            message=f"Błąd uruchamiania Fetch: {e}",
            source="exception"
        ).dict()

start_fetch = StructuredTool.from_function(
    name="start_fetch",
    description="Uruchamia Fetch: restart w razie potrzeby, czeka na cold-start, retryje /start, zwraca status.",
    func=_start_fetch,
    args_schema=EmptyInput,
    return_direct=True
)
