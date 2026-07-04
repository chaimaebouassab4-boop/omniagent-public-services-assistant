from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/chat/ping")
def ping_chat() -> dict:
    """Health ping for chat namespace."""
    return {"status": "success", "data": {"message": "chat online"}}
