#!/usr/bin/env python
# test_fetch.py
import os
from dotenv import load_dotenv
load_dotenv()  # wczytaj .env przed importami

import logging
import requests

def main():
    # Pobierz bazowy URL z ENV
    base_url = os.getenv("FETCH_BASE_URL", "https://fetch-2-0.onrender.com")
    logging.basicConfig(level=logging.INFO)

    # Lista end-pointów do weryfikacji połączenia
    endpoints = ["/status", "/start", "/status", "/stop"]
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            logging.info("Wysyłam GET %s", url)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            print(f"{ep} → {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            print(f"{ep} → Błąd połączenia lub HTTP: {e}")

if __name__ == "__main__":
    main()
