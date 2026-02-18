@"
from fastapi import FastAPI
from app.api import chat, cases, health

app = FastAPI(title="OMNIAGENT Government Assistant")

app.include_router(chat.router, prefix="/chat")
app.include_router(cases.router, prefix="/cases")
app.include_router(health.router, prefix="/health")

@app.get("/")
def root():
    return {"message": "OMNIAGENT API is running"}
"@ | Set-Content backend/main.py
