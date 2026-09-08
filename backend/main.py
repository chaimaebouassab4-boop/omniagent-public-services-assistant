from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# `cases` and `chat` implement the original enveloped API and are kept for
# reference; the omniagent frontend is served by the `omni` router below.
from app.api import auth, chat, health, omni  # noqa: F401
from app.core.config import settings
from app.core.seed_services import seed_admin, seed_services
from app.db.database import Base, SessionLocal, engine

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(omni.router)
app.include_router(health.router)


@app.on_event("startup")
async def startup_event() -> None:
    """Create DB tables and seed service definitions."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_services(db)
        seed_admin(db)
    finally:
        db.close()


@app.get("/")
async def root() -> dict:
    return {"message": "Omniagent Public Services API.."}
