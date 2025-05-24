import os
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

class FetchStatusInput(BaseModel):
    """Brak argumentów wejściowych."""
    pass


def _check_fetch_status(tool_input: FetchStatusInput) -> str:
    """
    Sprawdza status usługi Fetch poprzez endpoint /status.
    Zwraca:
      - "✅ Fetch działa"
      - "❌ Fetch nie działa (status: false)"
      - komunikat o błędzie przy wyjątku.
    """
    try:
        response = requests.get(f"{FETCH_BASE_URL}/status", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") is True:
            msg = "✅ Fetch działa"
        else:
            msg = "❌ Fetch nie działa (status: false)"
        logger.info("Status Fetch: %s", msg)
        return msg
    except Exception as e:
        report_error("FetchStatusTool", "check_fetch_status", e)
        logger.error("Błąd podczas sprawdzania statusu Fetch: %s", e, exc_info=True)
        return f"❌ Błąd podczas sprawdzania statusu Fetch: {e}"

# Rejestracja narzędzia LangChain
check_fetch_status = StructuredTool.from_function(
    name="check_fetch_status",
    description="Sprawdza status usługi Fetch poprzez endpoint /status",
    func=_check_fetch_status,
    args_schema=FetchStatusInput
)
