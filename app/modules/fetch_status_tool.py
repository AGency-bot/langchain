# app/modules/fetch_status_tool.py

import os
import requests
import logging
from pydantic import BaseModel
from langchain.tools import tool

logger = logging.getLogger(__name__)


class EmptyInput(BaseModel):
    """Pusty model wejściowy – wymagany przez LangChain."""
    pass


@tool(args_schema=EmptyInput, return_direct=True)
def check_fetch_status(_: EmptyInput) -> str:
    """
    Sprawdza, czy serwis Fetch jest aktywny, używając endpointu /status.
    Zwraca komunikat tekstowy.
    """
    base_url = os.getenv("FETCH_BASE_URL", "https://fetch-2-0.onrender.com")
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("running") or data.get("status") is True:
            return "✅ Fetch działa poprawnie."
        else:
            return "❌ Fetch nie działa (odpowiedź serwisu wskazuje na brak działania)."
    except Exception as e:
        logger.error("Błąd sprawdzania statusu Fetch: %s", e, exc_info=True)
        return f"❌ Błąd sprawdzania statusu Fetch: {e}"
