from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    access_code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    name: str | None = Field(None, max_length=255)

class DeleteAccountRequest(BaseModel):
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str