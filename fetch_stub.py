# fetch_stub.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
def status():
    return {"status": True}

@app.get("/stop")
def stop():
    return {"message": "stopped"}

@app.get("/start")
def start():
    return {"message": "started"}
