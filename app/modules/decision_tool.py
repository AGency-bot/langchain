import os
import logging
import pandas as pd
from pathlib import Path

from pydantic import BaseModel, Field
from langchain.tools import Tool

from app.modules.snapshot_sanitizer_tool import SnapshotSanitizerTool, SanitizerInput
from app.modules.mapper_tool import WojewodztwoMapperTool, MapperInput
from app.utils.error_reporter import report_error

# Konfiguracja loggera
logger = logging.getLogger(__name__)

class DecisionInput(BaseModel):
    """
    Wejściowy model danych: pojedynczy rekord JSON zlecenia.
    """
    record: dict = Field(..., description="Rekord JSON zawierający dane zlecenia z snapshotu")


def _decide_if_order_is_good(tool_input: DecisionInput) -> str:
    """
    Analizuje zlecenie i zwraca:
      - 'TAK' jeśli według tabeli preferencji wartość to 1,
      - 'NIE' jeśli wartość różna od 1,
      - komunikaty o błędach z prefiksem '❌'.
    """
    # 1. Sanityzacja rekordu
    try:
        sanity = SnapshotSanitizerTool().run(tool_input=SanitizerInput(record=tool_input.record))
        if sanity.startswith("❌"):
            logger.warning("Sanityzacja nieudana: %s", sanity)
            return f"❌ Rekord niepoprawny: {sanity}"
    except Exception as e:
        report_error("DecisionTool", "Sanityzacja rekordu", e)
        logger.error("Błąd sanityzacji: %s", e, exc_info=True)
        return f"❌ Błąd sanityzacji: {e}"

    # 2. Mapowanie województwa
    try:
        mapper_input = MapperInput(
            wojewodztwo_id=str(
                tool_input.record.get("cellValuesByColumnId", {})
                                  .get("fldCbMMnj7vuHlmsu", "")
            )
        )
        mapped = WojewodztwoMapperTool().run(tool_input=mapper_input)
        if mapped.startswith("❌"):
            logger.warning("Mapowanie nieudane: %s", mapped)
            return f"❌ Nie udało się rozpoznać województwa: {mapped}"
        wojewodztwo = mapped.strip().upper()
    except Exception as e:
        report_error("DecisionTool", "Mapowanie województwa", e)
        logger.error("Błąd mapowania województwa: %s", e, exc_info=True)
        return f"❌ Błąd mapowania województwa: {e}"

    # 3. Sprawdzanie tabeli preferencji
    try:
        excel_path = Path(
            os.getenv(
                "PREFERENCES_XLSX_PATH",
                "data/tablica_binarna.xlsx"
            )
        )
        if not excel_path.is_file():
            logger.error("Brak pliku preferencji: %s", excel_path)
            return f"❌ Brak pliku preferencji: {excel_path}"

        df = pd.read_excel(excel_path)
        df.columns = [str(col).strip().upper() for col in df.columns]

        segment = str(
            tool_input.record.get("cellValuesByColumnId", {})
                               .get("fldfEIZxM3O4pF3bW", "")
        ).strip().upper()

        if wojewodztwo not in df.columns:
            logger.warning("Brak kolumny województwo: %s", wojewodztwo)
            return f"❌ Województwo '{wojewodztwo}' nie występuje w tabeli"
        if segment not in df["SEGMENT"].values:
            logger.warning("Brak segmentu: %s", segment)
            return f"❌ Segment '{segment}' nie występuje w tabeli"

        value = df.loc[df["SEGMENT"] == segment, wojewodztwo].iat[0]
        result = "TAK" if value == 1 else "NIE"
        logger.info(
            "Decyzja dla segment %s i województwo %s: %s",
            segment, wojewodztwo, result
        )
        return result

    except Exception as e:
        report_error("DecisionTool", "Sprawdzanie tabeli preferencji", e)
        logger.error("Błąd przy sprawdzaniu preferencji: %s", e, exc_info=True)
        return f"❌ Błąd przy sprawdzaniu preferencji: {e}"

# Rejestracja narzędzia LangChain
decide_if_order_is_good = Tool.from_function(
    name="decide_if_order_is_good",
    description="Analizuje zlecenie i odpowiada TAK lub NIE, bazując na tabeli preferencji.",
    func=_decide_if_order_is_good,
    args_schema=DecisionInput,
    return_direct=True
)
