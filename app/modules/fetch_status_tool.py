# app/modules/fetch_status_tool.py

import logging
from typing import Optional
from pydantic import BaseModel
from langchain.tools import StructuredTool

from app.utils.fetch_api_client import FetchAPIClient
from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FetchStatusInput(BaseModel):
    """Brak argumentów wejściowych."""
    pass

def _check_fetch_status(tool_input: Optional[FetchStatusInput] = None) -> str:
    """
    Sprawdza, czy serwis fetch_2.0 działa, korzystając z FetchAPIClient.
    Zwraca "✅ Fetch działa" lub komunikat błędu/nieaktywności.
    """
    try:
        client = FetchAPIClient()
        data = client.get_status()
        logger.info("Otrzymano odpowiedź statusu: %s", data)
        running = data.get("running", data.get("status"))
        if running is True:
            return "✅ Fetch działa"
        return f"❌ Fetch nie działa (od serwisu: {data})"
    except Exception as e:
        report_error("FetchStatusTool", "check_fetch_status", e)
        logger.error("Błąd podczas sprawdzania statusu Fetch: %s", e, exc_info=True)
        return f"❌ Błąd podczas sprawdzania statusu Fetch: {e}"

check_fetch_status = StructuredTool.from_function(
    name="check_fetch_status",
    description="Sprawdza pole `running` (lub `status` dla kompatybilności) w odpowiedzi Fetch na `/status`.",
    func=_check_fetch_status,
    args_schema=FetchStatusInput,
    return_direct=True
)
