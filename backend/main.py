from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, chat, health
from app.core.config import settings
from app.core.seed_services import seed_services
from app.db.database import Base, SessionLocal, engine

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(cases.router)
app.include_router(chat.router)
app.include_router(health.router)


@app.on_event("startup")
async def startup_event() -> None:
    """Create DB tables and seed service definitions."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_services(db)
    finally:
        db.close()


@app.get("/")
async def root() -> dict:
    return {"message": "Omniagent Public Services API"}
