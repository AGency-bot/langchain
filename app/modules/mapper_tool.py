# app/modules/mapper_tool.py

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

from pydantic import BaseModel, Field

from app.utils.error_reporter import report_error
from langchain_core.tools import Tool  # upewnij się, że masz właściwy import

logger = logging.getLogger(__name__)

# Mapowanie kodów pocztowych na województwa
KOD_WOJ: Dict[str, str] = {
    "00": "MAZOWIECKIE", "01": "MAZOWIECKIE", "02": "MAZOWIECKIE", "03": "MAZOWIECKIE", "04": "MAZOWIECKIE",
    "05": "MAZOWIECKIE", "10": "WARMIŃSKO-MAZURSKIE", "15": "PODLASKIE", "20": "LUBELSKIE",
    "25": "ŚWIĘTOKRZYSKIE", "30": "MAŁOPOLSKIE", "31": "MAŁOPOLSKIE", "35": "PODKARPACKIE",
    "40": "ŚLĄSKIE", "45": "OPOLSKIE", "50": "DOLNOŚLĄSKIE", "51": "DOLNOŚLĄSKIE",
    "52": "DOLNOŚLĄSKIE", "53": "DOLNOŚLĄSKIE", "54": "DOLNOŚLĄSKIE", "60": "WIELKOPOLSKIE",
    "61": "WIELKOPOLSKIE", "65": "LUBUSKIE", "70": "ZACHODNIOPOMORSKIE",
    "71": "ZACHODNIOPOMORSKIE", "75": "ZACHODNIOPOMORSKIE", "80": "POMORSKIE",
    "81": "POMORSKIE", "82": "POMORSKIE", "83": "POMORSKIE", "84": "POMORSKIE",
    "85": "KUJAWSKO-POMORSKIE", "90": "ŁÓDZKIE", "91": "ŁÓDZKIE", "92": "ŁÓDZKIE",
    "93": "ŁÓDZKIE", "94": "ŁÓDZKIE"
}

_DEFAULT_MAP_PATH = Path("data") / "wojewodztwa_mapping.json"
_MAPPING_PATH = Path(os.getenv("WOJEWODZTWA_MAPPING_PATH", _DEFAULT_MAP_PATH))

_mapa_id_cache: Optional[Dict[str, str]] = None


class MapperInput(BaseModel):
    wojewodztwo_id: Optional[str] = Field(None, description="ID województwa")
    kod_pocztowy: Optional[str] = Field(None, description="Kod pocztowy w formacie NN-NNN")


def _load_id_map() -> Optional[Dict[str, str]]:
    global _mapa_id_cache
    if _mapa_id_cache is None:
        try:
            content = _MAPPING_PATH.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, dict):
                _mapa_id_cache = {str(k): str(v).strip().upper() for k, v in data.items()}
            else:
                logger.error("Nieprawidłowy format mapowania, oczekiwano dict.")
        except Exception as e:
            report_error("MapperTool", "_load_id_map", e)
            logger.error("Błąd wczytywania mapowania: %s", e, exc_info=True)
    return _mapa_id_cache


def resolve_wojewodztwo(wojewodztwo_id: Optional[str] = None, kod_pocztowy: Optional[str] = None) -> str:
    try:
        mapa = _load_id_map()
        if not mapa:
            return "❌ Błąd ładowania mapowania województw"

        if wojewodztwo_id:
            wid = wojewodztwo_id.strip()
            if wid in mapa:
                return mapa[wid]

        if kod_pocztowy:
            prefix = kod_pocztowy.replace("-", "").strip()[:2]
            if prefix in KOD_WOJ:
                return KOD_WOJ[prefix]

        return "❌ Nie udało się rozpoznać województwa"
    except Exception as e:
        report_error("MapperTool", "resolve_wojewodztwo", e)
        logger.error("Błąd mapowania: %s", e, exc_info=True)
        return f"❌ Błąd mapowania: {e}"

WojewodztwoMapperTool = Tool.from_function(
    name="resolve_wojewodztwo",
    description="Rozpoznaje nazwę województwa na podstawie ID lub kodu pocztowego.",
    func=resolve_wojewodztwo,
    args_schema=MapperInput,
    return_direct=True
)