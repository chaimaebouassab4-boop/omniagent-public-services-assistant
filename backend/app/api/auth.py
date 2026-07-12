import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["auth"])

MAX_PROFILE_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
CIN_MIME_TYPES = {"image/png", "application/pdf"}
PERSONAL_DOC_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp"}


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
        "cinFileName": Path(user.cin_file_path).name.split("_", 1)[-1] if user.cin_file_path else None,
        # Strip the server-side "path" key before exposing document metadata.
        "personalDocuments": [
            {key: value for key, value in doc.items() if key != "path"}
            for doc in (user.personal_documents or [])
        ],
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
# Profile documents (CIN + personal files)
# --------------------------------------------------------------------------- #
def _sanitize_upload_name(raw_name: str | None) -> str:
    base = Path(raw_name or "document").name
    cleaned = re.sub(r"[^\w.\- ]", "_", base).strip() or "document"
    return cleaned[:120]


async def _read_validated_upload(file: UploadFile, allowed_types: set[str]) -> tuple[bytes, str]:
    """Validate content type and size, returning the bytes and safe filename."""
    content_type = (file.content_type or "").lower()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(file_bytes) > MAX_PROFILE_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB limit",
        )
    return file_bytes, _sanitize_upload_name(file.filename)


def _profile_dir(user_id: str) -> Path:
    directory = Path(settings.upload_root) / "profiles" / user_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@router.post("/users/me/documents/cin", status_code=status.HTTP_201_CREATED)
async def upload_cin(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload the national identity card (PNG or PDF only); replaces any previous CIN."""
    file_bytes, safe_name = await _read_validated_upload(file, CIN_MIME_TYPES)

    previous = Path(current_user.cin_file_path) if current_user.cin_file_path else None
    stored_path = _profile_dir(current_user.id) / f"{uuid.uuid4().hex}_{safe_name}"
    stored_path.write_bytes(file_bytes)

    current_user.cin_file_path = str(stored_path)
    db.commit()
    db.refresh(current_user)

    if previous and previous.exists():
        previous.unlink(missing_ok=True)

    return serialize_user(current_user)


@router.post("/users/me/documents/personal", status_code=status.HTTP_201_CREATED)
async def upload_personal_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Attach a personal document (PDF or image) to the user's profile."""
    file_bytes, safe_name = await _read_validated_upload(file, PERSONAL_DOC_MIME_TYPES)

    stored_path = _profile_dir(current_user.id) / f"{uuid.uuid4().hex}_{safe_name}"
    stored_path.write_bytes(file_bytes)

    entry = {
        "id": uuid.uuid4().hex,
        "name": safe_name,
        "size": len(file_bytes),
        "mimeType": (file.content_type or "").lower(),
        "uploadedAt": datetime.now(UTC).isoformat(),
        "path": str(stored_path),
    }
    # Reassign (not mutate) so SQLAlchemy detects the JSON column change.
    current_user.personal_documents = [*(current_user.personal_documents or []), entry]
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
