# Dockerfile for langchain-agent

# 🐍 Use a lightweight Python 3.12 image
FROM python:3.12-slim

# 🛠️ Set working directory
WORKDIR /app

# 🔖 Copy dependency files separately to leverage Docker cache
COPY requirements.lock.txt requirements.txt ./

# 🌍 Install system dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        gcc \
        libpq-dev \
        curl \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 📦 Upgrade pip and install Python dependencies from lock file
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --require-hashes -r requirements.lock.txt

# 🗄️ Copy the rest of the application code
COPY . .

# 🌐 Expose port for FastAPI
EXPOSE 8000

# ▶️ Start the application with Uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
