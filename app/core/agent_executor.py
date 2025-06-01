# app/core/agent_executor.py

import os
import json
import logging
from pathlib import Path
from typing import Any

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.snapshot_tracker import SnapshotTracker
from app.tools.tool_registry import get_all_tools
from app.modules.s3_tool import s3_wrapper  # funkcja, nie Tool!

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Wczytanie promptu ---
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

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="intermediate_steps"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# --- LLM + Agent ---
llm = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.3
)

tools = get_all_tools()

agent = create_openai_functions_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False,
    return_intermediate_steps=True,
    handle_parsing_errors=True
)

# --- CLI ---
def run_agent_cli() -> None:
    """
    Tryb CLI do lokalnego testowania działania agenta.
    """
    try:
        logger.info("📦 Pobieram snapshot danych z S3...")
        raw = s3_wrapper({})

        logger.info("Raw z S3Tool: %s", raw)
        snapshot: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else raw

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
        new_records = tracker.filter_new_records(records)

        if not new_records:
            logger.info("🟡 Brak nowych rekordów do przetworzenia.")
            return

        logger.info("🟢 Wykryto %d nowych rekordów. Uruchamiam agenta...", len(new_records))
        result = agent_executor.invoke({"input": "Rozpocznij analizę i obsługę zleceń"})

        tracker.update_cache(records)
        logger.info("✅ WYNIK KOŃCOWY:\n%s", result)

    except Exception as e:
        logger.error("❌ Błąd główny agenta: %s", e, exc_info=True)

if __name__ == "__main__":
    run_agent_cli()
