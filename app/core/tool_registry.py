# app/core/tool_registry.py

from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel

# ✅ Poprawione importy
from app.modules.s3_tool import fetch_latest_snapshot
from app.modules.gmail_tool import send_gmail_email
from app.modules.mapper_tool import resolve_wojewodztwo
from app.modules.whatsapp_tool import _send_whatsapp
from app.modules.fetch_restart_tool import restart_fetch
from app.modules.fetch_status_tool import check_fetch_status
from app.modules.fetch_tool import resilient_fetch
from app.modules.decision_tool import decide_if_order_is_good
from app.modules.snapshot_sanitizer_tool import _sanityzuj_snapshot

# ✅ Pusty model wejściowy wymagany przez StructuredTool
class EmptyInput(BaseModel):
    pass

# ✅ Narzędzia LangChain Tools

s3_tool = StructuredTool.from_function(
    func=fetch_latest_snapshot,
    name="s3_tool",
    description="Zwraca najnowszy snapshot danych z S3 jako dict.",
    args_schema=EmptyInput,
    return_direct=True,
)

gmail_tool = Tool.from_function(
    name="gmail_tool",
    func=send_gmail_email,
    description="Wysyła e-mail z określonym tematem i treścią przez Gmail API.",
)

mapper_tool = Tool.from_function(
    name="mapuj_wojewodztwo",
    func=resolve_wojewodztwo,
    description="Mapuje ID województwa lub kod pocztowy na nazwę województwa.",
    return_direct=True,
)

whatsapp_template_tool = Tool.from_function(
    name="whatsapp_template_tool",
    func=_send_whatsapp,
    description="Wysyła wiadomość WhatsApp szablonową lub fallback tekst.",
    return_direct=True,
)

restart_fetch_tool = StructuredTool.from_function(
    func=restart_fetch,
    name="restart_fetch",
    description="Restartuje usługę Fetch (stop -> start -> status z retry).",
    args_schema=EmptyInput,
    return_direct=True,
)

fetch_status_tool = StructuredTool.from_function(
    func=check_fetch_status,
    name="check_fetch_status",
    description="Sprawdza status działania Fetch przez GET /status",
    args_schema=EmptyInput,
    return_direct=True,
)

fetch_tool = Tool.from_function(
    name="fetch_tool",
    func=resilient_fetch,
    description="Uruchamia Fetch. Jeśli nie działa, wykonuje restart i sprawdza status działania.",
    return_direct=True,
)

sanitizer_tool = Tool.from_function(
    name="snapshot_sanitizer_tool",
    func=_sanityzuj_snapshot,
    description="Sanityzuje snapshot – usuwa błędne rekordy lub zamienia puste dane.",
    return_direct=True,
)

decision_tool = Tool.from_function(
    name="decide_if_order_is_good",
    func=decide_if_order_is_good,
    description="Analizuje dane i ocenia, czy zlecenie jest wartościowe dla firmy.",
    return_direct=True,
)

# 🎯 Eksport wszystkich narzędzi
def get_all_tools() -> list[Tool]:
    return [
        s3_tool,
        gmail_tool,
        mapper_tool,
        whatsapp_template_tool,
        restart_fetch_tool,
        fetch_status_tool,
        fetch_tool,
        sanitizer_tool,
        decision_tool,
    ]
