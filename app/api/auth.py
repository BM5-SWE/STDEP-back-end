from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.db.session import SessionLocal
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest, TokenPair, UserResponse, UserUpdateRequest, DeleteAccountRequest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    hash_token, extract_user_id_from_token
)

router = APIRouter(tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=TokenPair, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # check existing email/username
    existing = db.execute(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already in use")

    print("PASSWORD REPR:", repr(payload.password))
    print("PASSWORD LEN:", len(payload.password))
    print("PASSWORD BYTES:", len(payload.password.encode("utf-8")))

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(sub=str(user.id))
    refresh, refresh_exp = create_refresh_token(sub=str(user.id))

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        expires_at=refresh_exp,
    ))
    db.commit()

    return TokenPair(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(sub=str(user.id))
    refresh, refresh_exp = create_refresh_token(sub=str(user.id))

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        expires_at=refresh_exp,
    ))
    db.commit()

    return TokenPair(access_token=access, refresh_token=refresh)

# get user info with user id (testing)
@router.get("/user/{user_id}", response_model=RegisterRequest)
def get_user_info(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # return password unhashed for testing
    return RegisterRequest(
        email=user.email,
        username=user.username,
        password=user.password_hash
    )

# ==================== USER PROFILE MANAGEMENT ====================

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """Extract current user from JWT token in Authorization header"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    
    user_id = extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    return user

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user's profile information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/user", response_model=UserResponse)
def update_user(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's email, username, or name"""
    # Check if new email is already taken
    if payload.email and payload.email != current_user.email:
        existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        current_user.email = payload.email
    
    # Check if new username is already taken
    if payload.username and payload.username != current_user.username:
        existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Username already in use")
        current_user.username = payload.username
    
    # Update name if provided
    if payload.name is not None:
        current_user.name = payload.name
    
    current_user.updated_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.delete("/user", status_code=204)
def delete_user(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account (requires password confirmation)"""
    # Verify password before deletion
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Delete refresh tokens associated with user
    db.execute(select(RefreshToken).where(RefreshToken.user_id == current_user.id))
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    
    # Delete user
    db.delete(current_user)
    db.commit()
    
    return None