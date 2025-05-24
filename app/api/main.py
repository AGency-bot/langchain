import os
import traceback
import logging

import openai

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.modules.gmail_tool import gmail_tool, GmailInput
from app.core.agent_executor import agent_executor
from app.utils.error_reporter import report_error
from app.version import AGENT_VERSION

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Załóż, że wszystkie wrażliwe dane (np. OPENAI_API_KEY) są ustawione w ENV z poziomu terminala
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY nie jest ustawione w środowisku")

# Inicjalizacja FastAPI
app = FastAPI(
    title="LangChain Agent Gateway",
    description="API dla uruchamiania agenta giełdowego",
    version=AGENT_VERSION
)

# 🔓 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

@app.get("/version", tags=["Monitoring"])
async def version_info():
    return {"version": AGENT_VERSION}

@app.get("/integration-check", tags=["Monitoring"])
async def integration_check():
    try:
        assert agent_executor is not None
        assert openai.api_key
        return {"status": "ok", "message": "Wszystkie komponenty są zintegrowane"}
    except AssertionError as e:
        return {"status": "error", "message": str(e)}

async def explain_error_with_ai(error_text: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem DevOps. Tłumacz błędy Python w zrozumiałą sposób."},
                {"role": "user", "content": f"Wyjaśnij ten wyjątek:\n{error_text}"}
            ],
            max_tokens=300,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as inner:
        logger.error("Błąd AI podczas analizy: %s", inner)
        return f"Wystąpił błąd podczas analizy przez AI: {inner}"

@app.post("/run-agent-llm", tags=["Agent"])
async def run_agent_llm():
    try:
        logger.info("🤖 Agent LLM startuje...")
        result = agent_executor.invoke({"input": "Rozpocznij analizę i obsługę zleceń"})
        return JSONResponse(content={"status": "Agent LLM zakończył działanie", "result": result}, status_code=200)
    except Exception as e:
        error_text = traceback.format_exc()
        ai_hint = await explain_error_with_ai(error_text)
        report = report_error("AgentLLM", "agent_executor.invoke()", e, analyze=False)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "ai_diagnosis": ai_hint,
                "error_report": report,
                "traceback": error_text
            }
        )

@app.post("/send-test-email", tags=["Agent"])
async def test_email():
    result = gmail_tool.run(
        tool_input=GmailInput(
            subject="Zlecenie 12345",
            body="Proszę o zlecenie."
        )
    )
    return JSONResponse(content={"status": "ok", "result": result})
