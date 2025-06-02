# app/core/tool_registry.py

from langchain.tools import StructuredTool
from app.modules.fetch_tool import start_fetch, EmptyInput as StartFetchInput
from app.modules.fetch_status_tool import check_fetch_status, EmptyInput as FetchStatusInput
from app.modules.fetch_restart_tool import restart_fetch, EmptyInput as FetchRestartInput
from app.modules.s3_tool import fetch_latest_snapshot, EmptyInput as S3Input
from app.modules.snapshot_sanitizer_tool import sanitize_record
from app.modules.mapper_tool import enrich_region_name
from app.modules.gmail_tool import send_gmail_message
from app.modules.whatsapp_tool import send_whatsapp_template
from app.modules.decision_tool import decision_engine

def get_all_tools():
    return [
        StructuredTool.from_function(
            func=start_fetch,
            name="start_fetch",
            description="Uruchamia narzędzie fetch_2.0 do pozyskania danych.",
            args_schema=StartFetchInput,
            return_direct=True
        ),
        StructuredTool.from_function(
            func=check_fetch_status,
            name="fetch_status_tool",
            description="Sprawdza status działania systemu fetch (działa lub nie działa).",
            args_schema=FetchStatusInput,
            return_direct=True
        ),
        StructuredTool.from_function(
            func=restart_fetch,
            name="fetch_restart_tool",
            description="Restartuje proces fetch_2.0.",
            args_schema=FetchRestartInput,
            return_direct=True
        ),
        StructuredTool.from_function(
            func=fetch_latest_snapshot,
            name="s3_tool",
            description="Zwraca najnowszy snapshot danych z S3 jako dict.",
            args_schema=S3Input,
            return_direct=True
        ),
        StructuredTool.from_function(
            func=sanitize_record,
            name="snapshot_sanitizer_tool",
            description="Waliduje i oczyszcza rekord snapshotu.",
            return_direct=True
        ),
        StructuredTool.from_function(
            func=enrich_region_name,
            name="mapper_tool",
            description="Uzupełnia nazwę województwa na podstawie kodu pocztowego lub ID.",
            return_direct=True
        ),
        StructuredTool.from_function(
            func=decision_engine,
            name="decision_tool",
            description="Ocena zlecenia wg preferencji klienta: TAK/NIE.",
            return_direct=True
        ),
        StructuredTool.from_function(
            func=send_gmail_message,
            name="gmail_tool",
            description="Wysyła e-mail do klienta z treścią oferty.",
            return_direct=True
        ),
        StructuredTool.from_function(
            func=send_whatsapp_template,
            name="whatsapp_template_tool",
            description="Wysyła wiadomość WhatsApp do klienta.",
            return_direct=True
        )
    ]
