# Azure CEO - Starter API (FastAPI)

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Azure CEO API running"}
