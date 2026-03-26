from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import hashlib
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(*, sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {"sub": sub, "type": "access", "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_refresh_token(*, sub: str) -> tuple[str, datetime]:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    payload = {"sub": sub, "type": "refresh", "exp": exp}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token, exp

def hash_token(token: str) -> str:
    # stable hash for DB lookup/revocation
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def decode_token(token: str) -> dict | None:
    """Decode JWT token and return payload, or None if invalid"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except JWTError:
        return None

def extract_user_id_from_token(token: str) -> uuid.UUID | None:
    """Extract user ID from JWT token"""
    payload = decode_token(token)
    if payload is None:
        return None
    try:
        return uuid.UUID(payload.get("sub"))
    except (ValueError, TypeError):
        return None