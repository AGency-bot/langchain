# app/modules/s3_tool.py

import os
import json
import logging
from typing import Any, Dict, Optional, List

import boto3
from pydantic import BaseModel, ValidationError
from langchain.tools import Tool

from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)

class EmptyInput(BaseModel):
    """Pusty model wejściowy, bo narzędzie nie potrzebuje żadnych dodatkowych danych."""
    pass

class S3ToolCore:
    """
    Klasa zawierająca logikę pobierania najnowszego snapshotu z AWS S3.
    """
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            logger.warning("S3_BUCKET_NAME nie jest ustawione w ENV.")
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
        )

    def _get_latest_keys(self) -> Optional[List[str]]:
        try:
            resp = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="motoassist/"
            )
            contents = resp.get("Contents", [])
            if len(contents) < 2:
                return None
            sorted_objs = sorted(
                contents,
                key=lambda o: o["LastModified"],
                reverse=True
            )
            return [sorted_objs[0]["Key"], sorted_objs[1]["Key"]]
        except Exception as e:
            report_error("S3Tool", "_get_latest_keys", e)
            logger.error("Błąd podczas pobierania kluczy snapshotów: %s", e, exc_info=True)
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
            logger.error("Nie można wczytać snapshotu '%s': %s", key, e, exc_info=True)
            raise

    def run(self) -> Dict[str, Any]:
        """
        Pobiera najnowszy snapshot z S3 i zwraca jako dict.
        Jeżeli wystąpi błąd, zwraca {'records': [], 'error': 'opis błędu'}.
        """
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
            logger.error("Błąd podczas ładowania snapshotu S3: %s", e, exc_info=True)
            return {"records": [], "error": str(e)}

# Funkcja‐opakowanie, którą zarejestrujemy jako LangChain Tool.
def s3_wrapper(raw_input: dict) -> Dict[str, Any]:
    """
    Wrapper, który przyjmuje słownik (lub instancję EmptyInput),
    weryfikuje go przez Pydantic i wywołuje S3ToolCore.run().
    Dzięki temu Tool.from_function będzie akceptować parametr pozycyjnie.
    """
    try:
        # Jeśli ktoś przekazał instancję EmptyInput, po prostu zignoruj walidację
        if isinstance(raw_input, EmptyInput):
            em = raw_input
        else:
            # Spróbuj sparsować surowe dane do modelu EmptyInput (w praktyce to zawsze będzie {} lub brak pól)
            em = EmptyInput.parse_obj(raw_input)
    except ValidationError as ve:
        report_error("S3Tool", "s3_wrapper.parse", ve)
        logger.error("Niepoprawne dane wejściowe do S3Tool (walidacja Pydantic): %s", ve, exc_info=True)
        # Zwróć pusty snapshot z opisem błędu
        return {"records": [], "error": f"Niepoprawne dane wejściowe: {ve}"}

    # Wywołaj właściwą logikę
    return S3ToolCore().run()

# Rejestracja narzędzia w LangChain, tak żeby móc wywoływać s3_tool.run(EmptyInput()) lub s3_tool.run({})
s3_tool = Tool.from_function(
    name="s3_tool",
    description="Zwraca najnowszy snapshot danych z S3 jako dict.",
    func=s3_wrapper,
    return_direct=True
)
