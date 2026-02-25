"""
Core security utilities — JWT helpers, password hashing (extensible for auth).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (for future auth integration)."""
    try:
        from jose import jwt
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    except ImportError:
        # jose not installed — return a stub token for development
        import base64, json
        return base64.b64encode(json.dumps(data).encode()).decode()


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None
