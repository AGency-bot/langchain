# app/tools/tool_registry.py

from langchain.tools import Tool

# 📦 Import refaktoryzowanych funkcji
from app.modules.s3_tool import s3_wrapper
from app.modules.gmail_tool import send_gmail_message
from app.modules.mapper_tool import resolve_wojewodztwo, MapperInput
from app.modules.whatsapp_tool import _send_whatsapp
from app.modules.fetch_tool import start_fetch
from app.modules.fetch_restart_tool import restart_fetch
from app.modules.fetch_status_tool import check_fetch_status
from app.modules.resilient_fetch_tool import resilient_fetch
from app.modules.decision_tool import decide_if_order_is_good

# ✅ Rejestracja narzędzi w formacie LangChain
s3_tool = Tool.from_function(
    name="s3_tool",
    func=s3_wrapper,
    description="Zwraca najnowszy snapshot danych z S3 jako dict.",
    return_direct=True,
)

gmail_tool = Tool.from_function(
    name="gmail_tool",
    func=send_gmail_message,
    description="Wysyła e-mail z określonym tematem, odbiorcą i treścią przez Gmail API.",
)

mapper_tool = Tool.from_function(
    name="mapuj_wojewodztwo",
    func=resolve_wojewodztwo,
    description="Mapuje ID województwa lub kod pocztowy na nazwę województwa.",
    args_schema=MapperInput,
    return_direct=True,
)

whatsapp_template_tool = Tool.from_function(
    name="whatsapp_template_tool",
    func=_send_whatsapp,
    description="Wysyła wiadomość WhatsApp szablonową lub fallback tekst.",
    return_direct=True,
)

fetch_tool = Tool.from_function(
    name="start_fetch",
    func=start_fetch,
    description="Uruchamia usługę Fetch, jeśli nie jest aktywna.",
)

restart_fetch_tool = Tool.from_function(
    name="restart_fetch",
    func=restart_fetch,
    description="Restartuje usługę Fetch (stop -> start -> status z retry).",
    return_direct=True,
)

fetch_status_tool = Tool.from_function(
    name="check_fetch_status",
    func=check_fetch_status,
    description="Sprawdza status działania Fetch przez GET /status",
    return_direct=True,
)

resilient_fetch_tool = Tool.from_function(
    name="resilient_fetch_tool",
    func=resilient_fetch,
    description="Uruchamia Fetch. Jeśli nie działa, wykonuje restart i sprawdza status działania.",
    return_direct=True,
)

decision_tool = Tool.from_function(
    name="decide_if_order_is_good",
    func=decide_if_order_is_good,
    description="Analizuje dane i ocenia, czy zlecenie jest wartościowe dla firmy.",
    return_direct=True,
)

# 🎯 Eksport zbiorczy
def get_all_tools() -> list[Tool]:
    return [
        s3_tool,
        gmail_tool,
        mapper_tool,
        whatsapp_template_tool,
        fetch_tool,
        restart_fetch_tool,
        fetch_status_tool,
        resilient_fetch_tool,
        decision_tool,
    ]
