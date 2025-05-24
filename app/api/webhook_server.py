import logging
import traceback

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.utils.error_reporter import report_error

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook")


def create_webhook_app() -> FastAPI:
    """Tworzy aplikację FastAPI nasłuchującą webhooki."""
    app = FastAPI(
        title="Webhook Listener",
        description="Obsługa wydarzeń z Webhooków (np. WhatsApp)",
        version="1.0.0"
    )

    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["Monitoring"])
    async def health_check():
        """Sprawdzenie stanu usługi."""
        return JSONResponse(content={"status": "ok"})

    @app.post("/webhook/whatsapp", tags=["Webhook"])
    async def whatsapp_webhook(
        from_: str = Form(..., alias="From"),
        body: str = Form(..., alias="Body")
    ):
        """Obsługa wiadomości przychodzących z WhatsApp via Twilio."""
        try:
            logger.info(f"📥 Wiadomość WhatsApp od {from_}: {body}")
            # Tutaj możesz zintegrować wywołanie agenta lub dalszą analizę
            return JSONResponse(content={"status": "received"}, status_code=200)
        except Exception as e:
            error_text = traceback.format_exc()
            # Zgłoś błąd do systemu raportowania
            report_error("WebhookServer", "whatsapp_webhook", e)
            logger.error(f"❌ Błąd webhooka WhatsApp: {e}")
            return JSONResponse(
                content={"status": "error", "message": str(e)},
                status_code=500
            )

    return app


# Tworzenie globalnej instancji aplikacji (do uruchomienia przez uvicorn)
app = create_webhook_app()
