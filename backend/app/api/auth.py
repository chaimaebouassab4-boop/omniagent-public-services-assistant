from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["auth"])


# --------------------------------------------------------------------------- #
# Request bodies
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class SignupRequest(BaseModel):
    fullName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    phone: str | None = None
    password: str = Field(..., min_length=6)


class UpdateProfileRequest(BaseModel):
    fullName: str | None = None
    phone: str | None = None


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name or "",
        "phone": user.phone,
        "isAdmin": user.is_admin,
    }


def auth_payload(user: User) -> dict:
    token = create_access_token(user_id=user.id, is_admin=user.is_admin)
    return {"token": token, "user": serialize_user(user)}


# --------------------------------------------------------------------------- #
# Citizen auth (raw JSON, consumed by the omniagent frontend)
# --------------------------------------------------------------------------- #
@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)) -> dict:
    """Register a new citizen account and return a JWT."""
    email = request.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
        full_name=request.fullName,
        phone=request.phone,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return auth_payload(user)


@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Authenticate a citizen (or admin) by email + password."""
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.password_hash or not verify_password(
        request.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return auth_payload(user)


@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the currently authenticated user's profile."""
    return serialize_user(current_user)


@router.patch("/auth/me")
async def update_me(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update the current user's profile fields."""
    if request.fullName is not None:
        current_user.full_name = request.fullName
    if request.phone is not None:
        current_user.phone = request.phone
    db.commit()
    db.refresh(current_user)
    return serialize_user(current_user)


# --------------------------------------------------------------------------- #
# Admin login (kept for the enveloped/legacy contract)
# --------------------------------------------------------------------------- #
@router.post("/admin/login")
async def admin_login(request: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Authenticate an administrator and return a JWT with the user profile."""
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_admin or not verify_password(
        request.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, is_admin=True)
    return {
        "status": "success",
        "data": {
            "tokens": {"accessToken": token, "tokenType": "bearer"},
            "user": {"id": user.id, "email": user.email, "isAdmin": user.is_admin},
        },
    }
