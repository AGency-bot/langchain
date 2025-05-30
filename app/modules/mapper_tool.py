import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

from pydantic import BaseModel, Field
from langchain.tools import Tool

from app.utils.error_reporter import report_error

# Konfiguracja loggera
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

# Ścieżka do pliku mapowania ID -> nazwa województwa
_DEFAULT_MAP_PATH = Path("data") / "wojewodztwa_mapping.json"
_MAPPING_PATH = Path(os.getenv("WOJEWODZTWA_MAPPING_PATH", _DEFAULT_MAP_PATH))
if not _MAPPING_PATH.is_file():
    logger.warning("Plik mapowania województw nie znaleziony: %s", _MAPPING_PATH)

# Cache mapowania
_mapa_id_cache: Optional[Dict[str, str]] = None

class MapperInput(BaseModel):
    """
    Wejściowy model: można podać 'wojewodztwo_id' lub 'kod_pocztowy'.
    """
    wojewodztwo_id: Optional[str] = Field(None, description="ID województwa z rekordu (np. selXYZ123)")
    kod_pocztowy: Optional[str] = Field(None, description="Kod pocztowy w formacie NN-NNN")


def _load_id_map() -> Optional[Dict[str, str]]:
    """
    Wczytuje JSON z mapowaniem ID -> nazwa województwa, buforuje wynik.
    """
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
            report_error("MapperTool", f"_load_id_map from {_MAPPING_PATH}", e)
            logger.error("Błąd wczytywania mapowania: %s", e, exc_info=True)
    return _mapa_id_cache


def _mapuj_wojewodztwo(tool_input: MapperInput) -> str:
    """
    Mapuje ID lub kod pocztowy na nazwę województwa.
    Zwraca czysty string nazwy lub komunikat z prefiksem '❌'.
    """
    try:
        mapa = _load_id_map()
        if not mapa:
            return "❌ Błąd ładowania mapowania województw"

        # Mapowanie po ID
        if tool_input.wojewodztwo_id:
            wid = tool_input.wojewodztwo_id.strip()
            if wid in mapa:
                return mapa[wid]

        # Mapowanie po kodzie pocztowym
        if tool_input.kod_pocztowy:
            prefix = tool_input.kod_pocztowy.replace('-', '').strip()[:2]
            if prefix in KOD_WOJ:
                return KOD_WOJ[prefix]

        return "❌ Nie udało się rozpoznać województwa"
    except Exception as e:
        report_error("MapperTool", "_mapuj_wojewodztwo", e)
        logger.error("Błąd mapowania województwa: %s", e, exc_info=True)
        return f"❌ Błąd mapowania województwa: {e}"


def resolve_wojewodztwo(value: str) -> Optional[str]:
    """
    Pomocnicza funkcja mapowania bez Pydantic.
    """
    if not value:
        return None
    try:
        mapa = _load_id_map()
        if mapa and value in mapa:
            return mapa[value]
        prefix = value.replace('-', '').strip()[:2]
        return KOD_WOJ.get(prefix)
    except Exception as e:
        report_error("MapperTool", "resolve_wojewodztwo", e)
        return None

# Rejestracja narzędzia LangChain
WojewodztwoMapperTool = Tool.from_function(
    name="mapuj_wojewodztwo",
    description="Mapuje ID województwa lub kod pocztowy na nazwę województwa.",
    func=_mapuj_wojewodztwo,
    args_schema=MapperInput,
    return_direct=True
)
