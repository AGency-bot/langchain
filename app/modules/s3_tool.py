import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from pydantic import BaseModel
from langchain.tools import StructuredTool

from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

class EmptyInput(BaseModel):
    """Brak danych wejściowych dla narzędzia S3Tool."""
    pass

class S3Tool:
    """
    Pobiera najnowszy snapshot z S3 jako dict.
    """
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            logger.warning("S3_BUCKET_NAME nie ustawione w ENV.")
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
        )

    def _get_latest_keys(self) -> Optional[List[str]]:
        try:
            resp = self.s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix="motoassist/"
            )
            contents = resp.get("Contents", [])
            if len(contents) < 2:
                return None
            sorted_objs = sorted(
                contents, key=lambda o: o["LastModified"], reverse=True
            )
            return [sorted_objs[0]["Key"], sorted_objs[1]["Key"]]
        except Exception as e:
            report_error("S3Tool", "_get_latest_keys", e)
            logger.error(
                "Błąd pobierania kluczy snapshotów: %s", e, exc_info=True
            )
            return None

    def _load_snapshot(self, key: str) -> Dict[str, Any]:
        try:
            obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            body = obj.get("Body")
            if not body:
                raise RuntimeError("Brak zawartości w obiekcie S3.")
            return json.loads(body.read())
        except Exception as e:
            report_error("S3Tool", f"_load_snapshot('{key}')", e)
            logger.error(
                "Nie można wczytać snapshotu '%s': %s", key, e, exc_info=True
            )
            raise

    def run(self, tool_input: EmptyInput) -> Dict[str, Any]:
        try:
            if not self.bucket_name:
                return {"records": [], "error": "Brak konfiguracji: S3_BUCKET_NAME"}

            keys = self._get_latest_keys()
            if not keys:
                return {"records": [], "error": "Brak wystarczających snapshotów w S3."}

            snapshot = self._load_snapshot(keys[0])
            return snapshot

        except Exception as e:
            report_error("S3Tool", "run", e)
            logger.error(
                "Błąd podczas ładowania snapshotu S3: %s", e, exc_info=True
            )
            return {"records": [], "error": str(e)}

# Rejestracja narzędzia LangChain
s3_tool = StructuredTool.from_function(
    name="s3_tool",
    description="Zwraca najnowszy snapshot danych z S3 jako dict.",
    func=S3Tool().run,
    args_schema=EmptyInput,
    return_direct=True
)
