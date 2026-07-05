"""
app/schemas/auth.py
-------------------
Pydantic schemas for the authentication API.
Includes forgot-password and reset-password schemas.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Body for POST /api/auth/signup."""
    name:     str      = Field(..., min_length=2, max_length=100)
    email:    EmailStr = Field(..., description="Valid email address")
    mobile:   str      = Field(..., min_length=10, max_length=15)
    password: str      = Field(..., min_length=6, description="Minimum 6 characters")


class UserLogin(BaseModel):
    """Body for POST /api/auth/login. Either email or mobile required."""
    email:    Optional[EmailStr] = None
    mobile:   Optional[str]      = None
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Body for POST /api/auth/forgot-password."""
    email: EmailStr = Field(..., description="Registered email address")


class ResetPasswordRequest(BaseModel):
    """Body for POST /api/auth/reset-password."""
    token:    str = Field(..., description="JWT reset token from email link")
    password: str = Field(
        ...,
        min_length = 8,
        max_length = 72,   # bcrypt hard limit
        description = "New password — 8 to 72 characters",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """User data in API responses. Never includes the password."""
    id:         str
    name:       str
    email:      str
    mobile:     str = ""
    created_at: str


class TokenResponse(BaseModel):
    """Returned by POST /api/auth/login on success."""
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


class MessageResponse(BaseModel):
    """Generic success/info message."""
    message: str
    user:    Optional[UserResponse] = None
