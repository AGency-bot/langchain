# app/modules/resilient_fetch_tool.py

import os
import requests
import logging
from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)

def resilient_fetch() -> str:
    """
    Uruchamia Fetch, a jeśli się nie powiedzie, restartuje go i sprawdza status.
    """
    base_url = os.getenv("FETCH_BASE_URL", "https://fetch-2-0.onrender.com")

    def _get(path: str) -> requests.Response:
        return requests.get(f"{base_url}{path}", timeout=10)

    try:
        logger.info("🚀 Próba uruchomienia Fetch...")
        _get("/start").raise_for_status()
        return "✅ Fetch został uruchomiony poprawnie."

    except Exception as e:
        logger.warning("⚠️ Fetch nie wystartował: %s", e)
        report_error("resilient_fetch_tool", "start", e)

        try:
            logger.info("🔄 Restartuję Fetch...")
            _get("/restart").raise_for_status()
        except Exception as restart_err:
            logger.error("❌ Nie udało się zrestartować Fetch: %s", restart_err, exc_info=True)
            report_error("resilient_fetch_tool", "restart", restart_err)
            return f"❌ Błąd restartu Fetch: {restart_err}"

        try:
            logger.info("🔍 Sprawdzam status Fetch...")
            response = _get("/status")
            response.raise_for_status()
            status_data = response.json()
            return f"🟢 Fetch zrestartowany i aktywny. Status: {status_data}"
        except Exception as status_err:
            logger.error("❌ Nie udało się sprawdzić statusu Fetch: %s", status_err, exc_info=True)
            report_error("resilient_fetch_tool", "status", status_err)
            return f"❌ Fetch został zrestartowany, ale status nieznany: {status_err}"
