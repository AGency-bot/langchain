import os
import traceback
import requests
import logging
import openai

log_file = "errors.log"
logger = logging.getLogger("agent")
DEBUGGER_ENDPOINT = os.getenv("DEBUGGER_ENDPOINT", "http://host.docker.internal:8001/report-error")

# Funkcja raportowania błędów z opcjonalną analizą GPT
def report_error(module: str, context: str = "", exception: Exception = None, analyze: bool = False):
    trace = traceback.format_exc()
    message = f"[{module}::{context}] ❌ {str(exception)}\n{trace}"

    # log do pliku
    try:
        with open(log_file, "a") as f:
            f.write(message + "\n")
    except Exception as log_fail:
        print(f"⚠️ Nie można zapisać do pliku logów: {log_fail}")

    # log do konsoli
    logger.error(message)

    # wysyłka do zewnętrznego debuggera
    try:
        payload = {
            "module": module,
            "context": context,
            "error": str(exception),
            "traceback": trace
        }
        res = requests.post(DEBUGGER_ENDPOINT, json=payload, timeout=5)
        if res.status_code == 200:
            print("✅ Błąd zgłoszony do debuggera.")
        else:
            print(f"⚠️ Debugger nie przyjął błędu: {res.status_code}")
    except Exception as e:
        print(f"❌ Nie można zgłosić błędu do debuggera: {e}")

    # analiza przez GPT (jeśli włączona)
    if analyze:
        try:
            gpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Jesteś asystentem DevOps. Analizuj błędy Pythona i sugeruj rozwiązania."},
                    {"role": "user", "content": f"Zanalizuj i zaproponuj rozwiązanie:\n{message}"}
                ],
                temperature=0.2,
                max_tokens=300
            )
            suggestion = gpt_response.choices[0].message.content.strip()
            logger.warning(f"💡 Sugestia GPT:\n{suggestion}")
            return suggestion
        except Exception as gpt_fail:
            logger.warning(f"⚠️ GPT analiza błędu się nie powiodła: {gpt_fail}")
            return None
