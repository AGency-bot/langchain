# app/modules/s3_tool.py

import os
import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from pydantic import BaseModel, ValidationError
from langchain.tools import Tool

from app.utils.error_reporter import report_error

logger = logging.getLogger(__name__)

class EmptyInput(BaseModel):
    """Model wejściowy – pusty, ponieważ narzędzie nie potrzebuje parametrów."""
    pass

def fetch_latest_snapshot(_: dict) -> Dict[str, Any]:
    """
    Pobiera najnowszy snapshot z S3 i zwraca jako dict.
    Jeśli wystąpi błąd – zwraca {'records': [], 'error': '...'}
    """
    try:
        bucket = os.getenv("S3_BUCKET_NAME")
        if not bucket:
            return {"records": [], "error": "Brak ENV S3_BUCKET_NAME"}

        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
        )

        # Szukamy dwóch najnowszych plików
        resp = s3.list_objects_v2(Bucket=bucket, Prefix="motoassist/")
        contents = resp.get("Contents", [])
        if len(contents) < 2:
            return {"records": [], "error": "Brak wystarczających snapshotów w S3."}

        sorted_objs = sorted(contents, key=lambda o: o["LastModified"], reverse=True)
        latest_key = sorted_objs[0]["Key"]

        # Pobieramy i parsujemy najnowszy snapshot
        obj = s3.get_object(Bucket=bucket, Key=latest_key)
        body = obj.get("Body")
        if not body:
            raise RuntimeError("Brak zawartości w obiekcie S3.")
        return json.loads(body.read())

    except Exception as e:
        report_error("s3_tool", "fetch_latest_snapshot", e)
        logger.error("❌ Błąd S3Tool: %s", e, exc_info=True)
        return {"records": [], "error": str(e)}

# Rejestracja jako LangChain Tool (poza logiką!)
s3_tool = Tool.from_function(
    name="s3_tool",
    description="Zwraca najnowszy snapshot danych z AWS S3 (format dict).",
    func=fetch_latest_snapshot,
    return_direct=True
)
