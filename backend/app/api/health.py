from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Simple liveness endpoint."""
    return {"status": "ok"}
