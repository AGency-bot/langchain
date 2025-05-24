import json
import logging
from pathlib import Path
from typing import Any, Dict, List

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnapshotTracker:
    """
    Śledzi już przetworzone rekordy, zapisując ich identyfikatory w pliku JSON.
    """
    def __init__(self, kind: str = "motoassist"):
        self.kind = kind
        # Upewnij się, że katalog na pliki cache istnieje
        self.cache_dir = Path("data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Ścieżka do pliku z zapisanymi id
        self.cache_path = self.cache_dir / f"{kind}_seen_records.json"
        self.seen_ids = self._load_seen_ids()

    def _load_seen_ids(self) -> List[str]:
        if self.cache_path.is_file():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return [str(i) for i in data]
                else:
                    logger.warning("Zawartość %s nie jest listą, restartuję cache.", self.cache_path)
            except json.JSONDecodeError as e:
                logger.error("Błąd dekodowania JSON w %s: %s", self.cache_path, e)
        return []

    def filter_new_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Zwraca listę rekordów, których identyfikatory nie były wcześniej przetworzone.
        """
        new_records: List[Dict[str, Any]] = []
        for record in records:
            record_id = record.get("id")
            if record_id:
                record_id_str = str(record_id)
                if record_id_str not in self.seen_ids:
                    new_records.append(record)
        logger.info("Nowych rekordów: %d", len(new_records))
        return new_records

    def update_cache(self, records: List[Dict[str, Any]]) -> None:
        """
        Aktualizuje cache, dodając nowe identyfikatory rekordów.
        """
        ids = {str(r.get("id")) for r in records if r.get("id")}
        combined = set(self.seen_ids) | ids
        try:
            # Zapis do pliku
            self.cache_path.write_text(json.dumps(list(combined), ensure_ascii=False, indent=2), encoding="utf-8")
            self.seen_ids = list(combined)
            logger.info("Zaktualizowano cache z %d rekordami.", len(self.seen_ids))
        except Exception as e:
            logger.error("Błąd zapisu cache do %s: %s", self.cache_path, e)
