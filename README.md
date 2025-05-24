# LangChain Agent for MotoAssist & Marcel

Inteligentny agent AI do automatycznego przetwarzania i obsługi zleceń pochodzących z systemów MotoAssist i Marcel. Agent wykorzystuje LangChain oraz wiele narzędzi integracyjnych do podejmowania decyzji, komunikacji i analizy danych zleceń.

---

## 📊 Sekwencja Przetwarzania

1. **Sprawdzenie statusu systemu Fetch**
   - Użyj `fetch_status_tool`, aby sprawdzić status systemu.
   - Jeśli nie działa: `fetch_restart_tool` + `start_fetch`.

2. **Pobranie snapshotu z S3**
   - `s3_tool` pobiera pliki JSON z najnowszymi zleceniami (`motoassist` lub `marcel`).

3. **Analiza danych**
   - `snapshot_sanitizer_tool`: sprawdza kompletność danych.
   - `mapper_tool`: mapuje ID województwa / kod pocztowy na nazwę.
   - `decision_tool`: korzysta z plików Excel z preferencjami, decyduje TAK/NIE.

4. **Komunikacja**
   - Jeśli TAK: `gmail_tool` wysyła e-mail do klienta.
   - Jeśli zlecenie już pozyskane (`marcel`): `whatsapp_tool` informuje użytkownika.

---

## 📝 Typy snapshotów

- `motoassist` — zlecenia do pozyskania
- `marcel` — zlecenia już pozyskane

---

## 📨 Komendy WhatsApp

- `praca start` → uruchamia agenta
- `praca stop` → zatrzymuje analizę

---

## 📊 Narzędzia

| Narzędzie              | Funkcja                                                   |
|--------------------------|------------------------------------------------------------|
| `fetch_status_tool`     | sprawdza działanie systemu fetch                        |
| `fetch_restart_tool`    | restartuje fetch                                           |
| `start_fetch`           | pobiera dane do analizy                                   |
| `s3_tool`               | pobiera pliki snapshot z S3                               |
| `snapshot_sanitizer`    | waliduje rekordy danych                                    |
| `mapper_tool`           | przekształca ID/kod pocztowy na województwo            |
| `decision_tool`         | podejmuje decyzję na podstawie tabeli preferencji       |
| `gmail_tool`            | wysyła e-mail, gdy decyzja to TAK                      |
| `whatsapp_tool`         | powiadamia użytkownika, gdy zlecenie zostanie pozyskane |

---

## ⚠️ Obsługa Błędów

- Agent informuje, jeśli którykolwiek etap zakończy się niepowodzeniem
- Nie kontynuuje pracy, jeśli snapshot jest pusty lub Fetch nie działa

---

## 🧠 Zachowanie agenta

- Działa sekwencyjnie i odpornie na błędy
- Nie wysyła wiadomości, gdy decyzja to "NIE"
- Potrafi odpowiedzieć na polecenia debugowania ("debuguj", "wyjaśnij błąd")

---

## 📁 Zależności

- Python 3.12
- FastAPI + Uvicorn
- LangChain: `langchain`, `langchain-core`, `langchain-community`
- Pydantic 2.x
- `boto3`, `openai`, `httpx`, `pandas`

---

## 📅 Uruchomienie lokalne

```bash
# 1. Buduj obraz Dockera
$ docker build -f Dockerfile.utf8 -t langchain-agent .

# 2. Uruchom z AWS regionem i dostępem do Secrets Managera
$ docker run -e AWS_REGION=eu-central-1 -p 8000:8000 langchain-agent
```

---

## 📑 Dokumentacja wewnętrzna

- Pliki danych: `data/*.xlsx` zawierają preferencje decyzyjne
- `agent.prompt.txt` został zintegrowany z tym README

---

## 🚀 Autorzy i utrzymanie

Projekt rozwijany jako agent biznesowy do automatyzacji decyzyjnej zleceń dla MotoAssist i Marcel.
Maintainer: [Twoje Imię lub Firma]
"# langchain" 
