# app/modules/fetch_restart_tool.py

import logging
import time
from typing import Optional
from pydantic import BaseModel
from langchain.tools import StructuredTool

from app.utils.fetch_api_client import FetchAPIClient
from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FetchRestartInput(BaseModel):
    """Brak danych wejściowych dla restartu Fetch."""
    pass

def _restart_fetch(tool_input: Optional[FetchRestartInput] = None) -> str:
    """
    Restartuje usługę Fetch:
      1. /stop z retry (3 próby)
      2. /start z retry (3 próby)
      3. Weryfikacja statusu /status z retry dla cold-start (10 prób)
    Zwraca tekstowy komunikat o wyniku operacji.
    """
    try:
        client = FetchAPIClient()

        # 1. Retry stop
        for i in range(3):
            logger.info("Restart – zatrzymuję Fetch (próba %d/3)", i+1)
            try:
                client.stop()
                break
            except Exception as e:
                logger.warning("Błąd przy /stop (próba %d): %s", i+1, e)
                time.sleep(2)
        else:
            return "❌ Nie udało się zatrzymać Fetch po 3 próbach"

        # Krótka pauza na wyłączenie
        time.sleep(2)

        # 2. Retry start
        for i in range(3):
            logger.info("Restart – uruchamiam ponownie Fetch (próba %d/3)", i+1)
            try:
                client.start()
                break
            except Exception as e:
                logger.warning("Błąd przy /start (próba %d): %s", i+1, e)
                time.sleep(2)
        else:
            return "❌ Nie udało się uruchomić Fetch po 3 próbach"

        # 3. Retry status dla cold-start
        for i in range(10):
            logger.info("Restart – sprawdzam status (%d/10)", i+1)
            try:
                data = client.get_status()
                running = data.get("running", data.get("status"))
                if running is True:
                    return "✅ Fetch został pomyślnie zrestartowany i działa"
            except Exception as e:
                logger.warning("Próba %d – błąd przy statusie: %s", i+1, e)
            time.sleep(3)

        return "⚠️ Fetch zrestartowany, ale nie odpowiedział poprawnie na /status"

    except Exception as e:
        report_error("FetchRestartTool", "restart_fetch", e)
        logger.error("Nieoczekiwany błąd podczas restartu Fetch: %s", e, exc_info=True)
        return f"❌ Nieoczekiwany błąd podczas restartu Fetch: {e}"

restart_fetch = StructuredTool.from_function(
    name="restart_fetch",
    description="Restartuje usługę Fetch: /stop → /start z retry i oczekuje na `/status`.",
    func=_restart_fetch,
    args_schema=FetchRestartInput,
    return_direct=True
)
