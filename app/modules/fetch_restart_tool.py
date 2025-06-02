# app/modules/fetch_restart_tool.py

import os
import requests
import logging
from pydantic import BaseModel
from langchain.tools import tool

from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)


class EmptyInput(BaseModel):
    """Pusty model wejściowy – wymagany przez LangChain."""
    pass


@tool(args_schema=EmptyInput, return_direct=True)
def restart_fetch(_: EmptyInput) -> str:
    """
    Restartuje serwis Fetch, używając endpointu /restart.
    Zwraca komunikat tekstowy.
    """
    base_url = os.getenv("FETCH_BASE_URL", "https://fetch-2-0.onrender.com")
    try:
        response = requests.get(f"{base_url}/restart", timeout=10)
        response.raise_for_status()
        return "🔁 Fetch został zrestartowany."
    except Exception as e:
        report_error("restart_fetch_tool", "restart_fetch", e)
        logger.error("❌ Błąd restartowania Fetch: %s", e, exc_info=True)
        return f"❌ Błąd restartowania Fetch: {e}"
