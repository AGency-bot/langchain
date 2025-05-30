# app/utils/fetch_api_client.py

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FetchAPIClient:
    """
    Klient HTTP dla serwisu fetch_2.0.
    Obsługuje /status, /start, /stop z jednolitą konfiguracją timeout i logowaniem.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url or os.getenv("FETCH_URL", "https://fetch-2-0.onrender.com")
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.info("HTTP GET %s", url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_status(self) -> Dict[str, Any]:
        """Zwraca JSON z pola 'running' lub dowolne inne klucze."""
        return self._get("/status")

    def start(self) -> Dict[str, Any]:
        """Wywołuje /start i zwraca JSON (np. {'status':'started'})."""
        return self._get("/start")

    def stop(self) -> Dict[str, Any]:
        """Wywołuje /stop i zwraca JSON (np. {'status':'stopping'})."""
        return self._get("/stop")
