import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from pydantic import BaseModel
from langchain_core.tools import StructuredTool

from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# Wejściowy model danych (brak argumentów)
class EmptyInput(BaseModel):
    """Brak danych wejściowych dla narzędzia S3Tool."""
    pass

class S3Tool:
    """
    Pobiera najnowszy snapshot (lub snapshots) z S3 jako JSON.
    """
    def __init__(self):
        # Nazwa bucketu powinna być ustawiona jako zmienna środowiskowa
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            logger.warning("S3_BUCKET_NAME nie ustawione w ENV.")
        # Tworzenie klienta S3
        self.s3 = self._get_s3_client()

    def _get_s3_client(self) -> Any:
        # Inicjalizacja klienta boto3 z poświadczeniami z ENV
        return boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
        )

    def _get_latest_keys(self) -> Optional[List[str]]:
        """
        Zwraca klucze do dwóch najnowszych obiektów w bucketcie (prefix 'motoassist/').
        """
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="motoassist/")
            contents = resp.get("Contents", [])
            if len(contents) < 2:
                return None
            # Sortowanie wg. daty modyfikacji malejąco
            sorted_objs = sorted(contents, key=lambda obj: obj["LastModified"], reverse=True)
            return [sorted_objs[0]["Key"], sorted_objs[1]["Key"]]
        except Exception as e:
            report_error("S3Tool", "_get_latest_keys", e)
            logger.error("❌ Błąd pobierania kluczy snapshotów: %s", e, exc_info=True)
            return None

    def _load_snapshot(self, key: str) -> Dict[str, Any]:
        """
        Wczytuje obiekt JSON spod podanego klucza i zwraca jako dict.
        """
        try:
            obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            body = obj.get("Body")
            if not body:
                raise RuntimeError("Brak zawartości w obiekcie S3.")
            data = json.loads(body.read())
            return data
        except Exception as e:
            report_error("S3Tool", f"_load_snapshot('{key}')", e)
            logger.error("❌ Nie można wczytać snapshotu '%s': %s", key, e, exc_info=True)
            raise

    def run(self, tool_input: EmptyInput) -> str:
        """
        Główna metoda wykonywana przez LangChain: zwraca JSON string snapshotu.
        """
        try:
            if not self.bucket_name:
                err = {"records": [], "error": "Brak konfiguracji: S3_BUCKET_NAME"}
                return json.dumps(err, ensure_ascii=False)

            keys = self._get_latest_keys()
            if not keys:
                err = {"records": [], "error": "Brak wystarczających snapshotów w S3."}
                return json.dumps(err, ensure_ascii=False)

            # Wczytaj najnowszy snapshot
            snapshot = self._load_snapshot(keys[0])
            return json.dumps(snapshot, ensure_ascii=False)

        except Exception as e:
            report_error("S3Tool", "run", e)
            logger.error("❌ Błąd podczas ładowania snapshotu S3: %s", e, exc_info=True)
            err = {"records": [], "error": f"Błąd: {str(e)}"}
            return json.dumps(err, ensure_ascii=False)

# Rejestracja narzędzia LangChain
s3_tool = StructuredTool.from_function(
    name="s3_tool",
    description="Zwraca najnowszy snapshot danych z S3 (format JSON).",
    func=S3Tool().run,
    args_schema=EmptyInput
)