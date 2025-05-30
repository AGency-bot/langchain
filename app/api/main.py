# app/api/main.py

from dotenv import load_dotenv
load_dotenv()  # load .env before other imports

import os
import traceback
import logging

import openai
from openai import AsyncOpenAI
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.messaging_response import MessagingResponse

from app.modules.gmail_tool import gmail_tool, GmailInput
from app.utils.error_reporter import report_error
from app.core.agent_executor import agent_executor
from app.version import AGENT_VERSION
from app.state.agent_state import agent_state

# ------------------------------------------------
# Load and configure OpenAI client asynchronously
# ------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.getLogger(__name__).warning("OPENAI_API_KEY nie jest ustawione w środowisku")

_ai_client = AsyncOpenAI(api_key=openai.api_key)

# ------------------------------------------------
# 1) Unified logging configuration
# ------------------------------------------------
default_level = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
logging.basicConfig(
    level=getattr(logging, default_level, logging.INFO),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# ------------------------------------------------
# 2) Initialize FastAPI with CORS
# ------------------------------------------------
app = FastAPI(
    title="LangChain Agent Gateway",
    description="API dla uruchamiania agenta AI",
    version=AGENT_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------
# 3) Global exception handler for all endpoints
# ------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    report = report_error("main", "global_exception_handler", exc, analyze=False)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "error_report": report
        },
    )

# ------------------------------------------------
# 4) Monitoring endpoints
# ------------------------------------------------
@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

@app.get("/version", tags=["Monitoring"])
async def version_info():
    return {"version": AGENT_VERSION}

@app.get("/integration-check", tags=["Monitoring"])
async def integration_check():
    try:
        assert agent_executor is not None, "Brak agent_executor"
        assert openai.api_key, "Brak OPENAI_API_KEY"
        return {"status": "ok", "message": "Wszystkie komponenty są zintegrowane"}
    except AssertionError as e:
        logger.error("Błąd integracji: %s", e)
        report = report_error("main", "integration_check", e, analyze=False)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "error_report": report}
        )

# ------------------------------------------------
# 5) AI-assisted error explanation helper (updated)
# ------------------------------------------------
async def explain_error_with_ai(error_text: str) -> str:
    try:
        response = await _ai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem DevOps. Tłumacz błędy Python."},
                {"role": "user",   "content": f"Wyjaśnij ten wyjątek:\n{error_text}"}
            ],
            max_tokens=300,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as inner:
        logger.error("Błąd AI podczas analizy: %s", inner, exc_info=True)
        return f"❌ Błąd AI: {inner}"

# ------------------------------------------------
# 6) Main agent endpoint
# ------------------------------------------------
@app.post("/run-agent-llm", tags=["Agent"])
async def run_agent_llm():
    try:
        logger.info("🤖 Agent LLM startuje...")
        result = agent_executor.invoke({"input": "Rozpocznij analizę i obsługę zleceń"})
        output_text = result.get("output") if isinstance(result, dict) else str(result)
        return JSONResponse(status_code=200, content={"status": "ok", "result": output_text})
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
            },
        )

# ------------------------------------------------
# 7) Test email endpoint
# ------------------------------------------------
@app.post("/send-test-email", tags=["Agent"])
async def test_email():
    result = gmail_tool.run(
        tool_input=GmailInput(subject="Zlecenie 12345", body="Proszę o zlecenie.")
    )
    return JSONResponse(content={"status": "ok", "result": result})

# ------------------------------------------------
# 8) WhatsApp webhook
# ------------------------------------------------
@app.post("/whatsapp/webhook", response_class=PlainTextResponse)
async def whatsapp_webhook(
    body: str = Form(..., alias="Body"),
    from_number: str = Form(..., alias="From"),
):
    resp = MessagingResponse()
    cmd = body.strip().lower()
    if cmd == "praca start":
        agent_state.start()
        resp.message("✅ Agent uruchomiony.")
    elif cmd == "praca stop":
        agent_state.stop()
        resp.message("⏸️ Agent zatrzymany.")
    else:
        resp.message("❓ Nie rozumiem. Dostępne: praca start, praca stop")
    return PlainTextResponse(str(resp), media_type="application/xml")

# ------------------------------------------------
# 9) Uvicorn entrypoint for local/dev
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=port, log_level=default_level.lower())
