# app/api/v1/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# This tells FastAPI where tokens are obtained (used for docs + dependency)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


# ---------- Pydantic models ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Fake user store for now ----------

FAKE_USER_DB = {
    "test@example.com": {
        "email": "test@example.com",
        "hashed_password": "password",  # TODO: replace with real hashing later
        "full_name": "Test User",
    }
}


def verify_user(email: str, password: str):
    """Very basic fake verification for now."""
    user = FAKE_USER_DB.get(email)
    if not user:
        return None
    if password != user["hashed_password"]:
        return None
    return user


# ---------- Routes ----------

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """
    Accept email + password, validate, and return a signed JWT.
    """
    user = verify_user(payload.email, payload.password)
    if not user:
        # matches what your frontend expects (`detail` / `message`)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # the "sub" (subject) claim is typically the user id or email
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=token)


# Dependency to use on protected endpoints
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decode JWT from Authorization header and return user info (for now just email).
    """
    try:
        payload = decode_access_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise ValueError("Missing subject in token")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = FAKE_USER_DB.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user
