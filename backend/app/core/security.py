from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models import User


@dataclass
class TokenPayload:
    sub: str
    is_admin: bool


def create_access_token(user_id: str, is_admin: bool = False, expires_minutes: int = 60) -> str:
    """Creates a signed JWT for API authentication."""
    expires = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": user_id, "is_admin": is_admin, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Decodes and validates the JWT payload."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub claim")
        return TokenPayload(sub=user_id, is_admin=bool(payload.get("is_admin", False)))
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        ) from exc


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """Resolves the current user from Bearer JWT or creates a local dev fallback."""
    if not authorization:
        user = db.query(User).filter(User.email == "citizen@demo.local").first()
        if user is None:
            user = User(email="citizen@demo.local", is_admin=False)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    payload = decode_access_token(parts[1])
    user = db.query(User).filter(User.id == payload.sub).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
