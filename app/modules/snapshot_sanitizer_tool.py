import logging

from pydantic import BaseModel, Field
from langchain.tools import Tool

from app.utils.error_reporter import report_error

# 📜 Klucze pól z rekordu Airtable
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
    Weryfikuje poprawność rekordu ze snapshotu:
      - Sprawdza obecność pól segmentu i województwa.
      - Zwraca '✅ Rekord wygląda poprawnie' lub komunikat '❌ ...'.
    """
    try:
        cell = tool_input.record.get("cellValuesByColumnId")
        if not isinstance(cell, dict) or not cell:
            return "❌ Brak danych w polu 'cellValuesByColumnId'"

        segment = str(cell.get(SEGMENT_FIELD_ID, "")).strip()
        wojewodztwo = str(cell.get(WOJEWODZTWO_FIELD_ID, "")).strip()

        if not segment:
            return "❌ Brak wartości segmentu pojazdu"
        if not wojewodztwo:
            return "❌ Brak województwa lub kodu pocztowego"

        return "✅ Rekord wygląda poprawnie"

    except Exception as e:
        report_error("SnapshotSanitizerTool", "sanityzuj_snapshot", e)
        logger.error("Błąd sanityzacji snapshotu: %s", e, exc_info=True)
        return f"❌ Błąd sanityzacji: {e}"

# Rejestracja narzędzia LangChain
SnapshotSanitizerTool = Tool.from_function(
    name="sanityzuj_snapshot",
    description="Weryfikuje poprawność rekordu snapshotu: czy zawiera wymagane pola segmentu i województwa.",
    func=_sanityzuj_snapshot,
    args_schema=SanitizerInput,
    return_direct=True
)
