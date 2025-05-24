import os
import json
import logging
from pathlib import Path

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.modules.fetch_tool import start_fetch, EmptyInput
from app.modules.s3_tool import s3_tool
from app.modules.decision_tool import decide_if_order_is_good
from app.modules.gmail_tool import gmail_tool
from app.core.snapshot_tracker import SnapshotTracker

# Konfiguracja logowania\logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista dostępnych narzędzi
available_tools: list[Tool] = [
    start_fetch,
    s3_tool,
    decide_if_order_is_good,
    gmail_tool,
    # whatsapp_tool (planowany)
]

# Wczytywanie promptu systemowego
prompt_path = Path(os.getenv("PROMPT_PATH", "data/agent.prompt.txt"))
if prompt_path.is_file():
    try:
        system_prompt = prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("❌ Błąd odczytu promptu: %s", e)
        system_prompt = "Agent startowy (domyślna konfiguracja)."
else:
    logger.warning("Prompt nie znaleziony pod ścieżką %s, używam domyślnego.", prompt_path)
    system_prompt = "Agent startowy (domyślna konfiguracja)."

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Konfiguracja modelu LLM
model_name = os.getenv("OPENAI_MODEL", "gpt-4")
llm = ChatOpenAI(model=model_name, temperature=0.3)

agent = create_openai_functions_agent(
    llm=llm,
    prompt=prompt,
    tools=available_tools
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=available_tools,
    verbose=True,
    return_intermediate_steps=True,
    handle_parsing_errors=True
)

def run_agent_cli():
    """
    Główna logika uruchamiana w trybie CLI.
    """
    try:
        raw_result = s3_tool.run(tool_input=EmptyInput())
        snapshot = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

        records = snapshot.get("records", [])
        kind = "marcel" if any("marcel" in str(v).lower() for v in snapshot.values()) else "motoassist"
        tracker = SnapshotTracker(kind=kind)

        new_records = tracker.filter_new_records(records)

        if not new_records:
            logger.info("🔍 Brak nowych zleceń do przetworzenia.")
        else:
            logger.info("🆕 Wykryto %d nowych rekordów. Rozpoczynam analizę...", len(new_records))
            result = agent_executor.invoke({"input": "Rozpocznij analizę i obsługę zleceń"})
            tracker.update_cache(records)
            logger.info("=== WYNIK KOŃCOWY ===\n%s", result)
    except Exception as e:
        logger.error("❌ Błąd główny agenta: %s", e, exc_info=True)

if __name__ == "__main__":
    run_agent_cli()
