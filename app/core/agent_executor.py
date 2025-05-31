# app/core/agent_executor.py

import os
import json
import logging
from pathlib import Path

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.modules.fetch_tool import start_fetch, EmptyInput
from app.modules.s3_tool import s3_tool
from app.modules.decision_tool import decide_if_order_is_good
from app.modules.gmail_tool import gmail_tool
from app.modules.whatsapp_tool import whatsapp_template_tool
from app.core.snapshot_tracker import SnapshotTracker

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista dostępnych narzędzi
available_tools: list[Tool] = [
    start_fetch,
    s3_tool,
    decide_if_order_is_good,
    gmail_tool,
    whatsapp_template_tool,
]

# Wczytanie promptu systemowego
prompt_path = Path(os.getenv("PROMPT_PATH", "data/agent.prompt.txt"))
if prompt_path.is_file():
    try:
        system_prompt = prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Błąd odczytu promptu: %s", e, exc_info=True)
        system_prompt = "Agent startowy (domyślna konfiguracja)."
else:
    logger.warning("Prompt nie znaleziony pod ścieżką %s, używam domyślnego.", prompt_path)
    system_prompt = "Agent startowy (domyślna konfiguracja)."

# Szablon konwersacji z placeholderami
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="intermediate_steps"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Inicjalizacja LLM (naprawiony parametr model_name)
model_name = os.getenv("OPENAI_MODEL", "gpt-4")
llm = ChatOpenAI(model_name=model_name, temperature=0.3)

# Tworzenie agenta
agent = create_openai_functions_agent(
    llm=llm,
    prompt=prompt,
    tools=available_tools
)

# Executor agenta
agent_executor = AgentExecutor(
    agent=agent,
    tools=available_tools,
    verbose=False,
    return_intermediate_steps=True,
    handle_parsing_errors=True
)

def run_agent_cli():
    """
    Tryb CLI do lokalnego testowania działania agenta.
    """
    try:
        # 1) Pobranie snapshotu z S3 (jako dict)
        raw = s3_tool.run(tool_input=EmptyInput())
        logger.info("Raw z S3Tool: %s", raw)

        # 2) Parsowanie JSON (jeśli to string) lub użycie dict bezpośrednio
        if isinstance(raw, str):
            try:
                snapshot = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.error("Niepoprawny JSON z S3: %s", e, exc_info=True)
                return
        else:
            snapshot = raw

        # 3) Upewnij się, że istnieje klucz "records"
        if "records" not in snapshot:
            logger.error("Brak klucza 'records' w snapshotcie: %s", snapshot)
            return

        records = snapshot.get("records", [])
        kind = (
            "marcel"
            if any("marcel" in str(v).lower() for v in snapshot.values())
            else "motoassist"
        )
        tracker = SnapshotTracker(kind=kind)

        # 4) Filtracja nowych rekordów
        new_records = tracker.filter_new_records(records)
        if not new_records:
            logger.info("Brak nowych rekordów do przetworzenia.")
            return

        logger.info("Wykryto %d nowych rekordów. Uruchamiam agenta...", len(new_records))
        result = agent_executor.invoke({"input": "Rozpocznij analizę i obsługę zleceń"})
        tracker.update_cache(records)
        logger.info("=== WYNIK KOŃCOWY ===\n%s", result)

    except Exception as e:
        logger.error("Błąd główny agenta: %s", e, exc_info=True)

if __name__ == "__main__":
    run_agent_cli()
