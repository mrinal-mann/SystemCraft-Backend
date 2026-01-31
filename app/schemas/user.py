"""
User Schemas

Pydantic models for user-related request/response validation.

Design Pattern:
- Create: for creating new resources (no id, timestamps)
- Update: for partial updates (all fields optional)
- Response: for API responses (includes id, timestamps)
- InDB: extends Response with sensitive fields (internal use only)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ============== Request Schemas ==============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


# ============== Response Schemas ==============

class UserResponse(BaseModel):
    """Schema for user in API responses (excludes password)."""
    id: int
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enables ORM mode (reads from SQLAlchemy models)


# ============== Token Schemas ==============

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded JWT payload."""
    sub: Optional[str] = None  # Subject (user id)
    exp: Optional[int] = None  # Expiration time
