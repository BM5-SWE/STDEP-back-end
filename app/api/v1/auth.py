# app/api/v1/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import SessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])

# This tells FastAPI where tokens are obtained (used for docs + dependency)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

# Valid access codes for registration
VALID_ACCESS_CODES = {"000000", "123456", "654321"}  # TODO: load from database or config


# ---------- Pydantic models ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    access_code: str  # 6-digit code
    email: EmailStr
    password: str
    confirm_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_user(email: str, password: str, db: Session):
    """Verify user credentials from database."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------- Routes ----------

@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with access code, email, and password.
    Returns a JWT token on success.
    """
    # Validate access code
    if payload.access_code not in VALID_ACCESS_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid access code",
        )

    # Check if passwords match
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(payload.password)
    new_user = User(
        email=payload.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Accept email + password, validate, and return a signed JWT.
    """
    user = verify_user(payload.email, payload.password, db)
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
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=token)


# Dependency to use on protected endpoints
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return user

    return user
