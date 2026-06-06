# JWT token management
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt

from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.auth.SECRET_KEY,
        algorithm=settings.auth.ALGORITHM,
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT access token."""
    return jwt.decode(
        token,
        settings.auth.SECRET_KEY,
        algorithms=[settings.auth.ALGORITHM],
    )
