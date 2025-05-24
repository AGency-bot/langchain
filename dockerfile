# 🐍 Wybierz lekkie środowisko z Pythona 3.12
FROM python:3.12-slim

# 🛠️ Ustaw katalog roboczy
WORKDIR /app

# 📦 Skopiuj pliki aplikacji i zależności
COPY requirements.txt requirements.lock.txt ./
COPY . .

# 🌍 Zainstaluj zależności systemowe
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 📦 Zainstaluj zależności Pythona z requirements.txt (lock jako kontrola)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip check

# 🌐 Port dla Render/FastAPI
EXPOSE 8000

# ▶️ Uruchom aplikację FastAPI przez Uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
