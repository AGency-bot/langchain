import logging

from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.utils.error_reporter import report_error

# 📜 Klucze pól z rekordu Airtable (łatwe do zmiany)
SEGMENT_FIELD_ID = "fldfEIZxM3O4pF3bW"
WOJEWODZTWO_FIELD_ID = "fldCbMMnj7vuHlmsu"

# Konfiguracja loggera
logger = logging.getLogger(__name__)

class SanitizerInput(BaseModel):
    """
    Model wejściowy: rekord JSON do sanityzacji.
    """
    record: dict = Field(..., description="Rekord JSON do sanityzacji")


def _sanityzuj_snapshot(tool_input: SanitizerInput) -> str:
    """
    Weryfikuje, czy rekord zawiera wymagane pola segmentu i województwa.
    Zwraca:
      - '✅ Rekord wygląda poprawnie'
      - '❌ ...' z opisem brakującego pola lub błędu
    """
    try:
        record = tool_input.record
        cell = record.get("cellValuesByColumnId")

        if not isinstance(cell, dict) or not cell:
            logger.warning("Brak danych w polu 'cellValuesByColumnId'.")
            return "❌ Brak danych w polu 'cellValuesByColumnId'"

        segment = str(cell.get(SEGMENT_FIELD_ID, "")).strip()
        wojewodztwo = str(cell.get(WOJEWODZTWO_FIELD_ID, "")).strip()

        if not segment:
            logger.warning("Brak wartości segmentu pojazdu.")
            return "❌ Brak wartości segmentu pojazdu"
        if not wojewodztwo:
            logger.warning("Brak województwa lub kodu pocztowego.")
            return "❌ Brak województwa lub kodu pocztowego"

        return "✅ Rekord wygląda poprawnie"

    except Exception as e:
        report_error("SnapshotSanitizerTool", "sanityzuj_snapshot", e)
        logger.error("Błąd sanityzacji snapshotu: %s", e, exc_info=True)
        return f"❌ Błąd sanityzacji: {e}"

# Rejestracja narzędzia LangChain
SnapshotSanitizerTool = Tool.from_function(
    name="sanityzuj_snapshot",
    description="Weryfikuje poprawność rekordu snapshotu: czy zawiera wymagane pola.",
    func=_sanityzuj_snapshot,
    args_schema=SanitizerInput
)
