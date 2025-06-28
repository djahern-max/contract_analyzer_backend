# schemas/auth.py
"""
Authentication-related Pydantic schemas.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from .base import BaseResponse, TimestampMixin


class UserCreate(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""

    username: str  # email
    password: str


class UserResponse(BaseResponse, TimestampMixin):
    """Schema for user information in responses"""

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class Token(BaseModel):
    """Schema for authentication tokens"""

    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    """Schema for token payload data"""

    username: Optional[str] = None
    user_id: Optional[int] = None


class PasswordReset(BaseModel):
    """Schema for password reset requests"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""

    token: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
