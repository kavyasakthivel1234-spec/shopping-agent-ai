"""
app/routes/auth.py
------------------
FastAPI router for all authentication endpoints.

Endpoints:
  POST /api/auth/signup           — register: name / email / mobile / password
  POST /api/auth/login            — login by email or mobile + password
  GET  /api/auth/profile          — protected: return current user
  POST /api/auth/forgot-password  — request a password reset email
  POST /api/auth/reset-password   — complete reset using JWT token
"""

import logging

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb         import get_database
from app.schemas.auth             import (
    UserCreate, UserLogin,
    ForgotPasswordRequest, ResetPasswordRequest,
    UserResponse, TokenResponse, MessageResponse,
)
from app.services.auth_service    import signup_user, login_user
from app.services.password_service import (
    initiate_password_reset,
    complete_password_reset,
)
from app.utils.security           import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------------------

@router.post(
    "/signup",
    response_model = MessageResponse,
    status_code    = status.HTTP_201_CREATED,
    summary        = "Register a new user account",
)
async def signup(data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Register a new user (name, email, mobile, password).
    Password is bcrypt-hashed before storage.
    Returns 409 if email or mobile already exists.
    """
    user = await signup_user(data, db)
    return MessageResponse(
        message = "Account created successfully. You can now sign in.",
        user    = UserResponse(**user),
    )


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model = TokenResponse,
    summary        = "Login and receive a JWT access token",
)
async def login(data: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Authenticate with email or mobile + password.
    Returns a signed JWT valid for 7 days.
    """
    result = await login_user(data, db)
    return TokenResponse(
        access_token = result["access_token"],
        token_type   = result["token_type"],
        user         = UserResponse(**result["user"]),
    )


# ---------------------------------------------------------------------------
# GET /api/auth/profile  (protected)
# ---------------------------------------------------------------------------

@router.get(
    "/profile",
    response_model = UserResponse,
    summary        = "Get the authenticated user's profile",
)
async def profile(current_user: dict = Depends(get_current_user)):
    """Requires a valid Authorization: Bearer <token> header."""
    return UserResponse(**current_user)


# ---------------------------------------------------------------------------
# POST /api/auth/forgot-password
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password",
    response_model = MessageResponse,
    summary        = "Request a password reset email",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db:   AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Accepts an email address and sends a reset link if the account exists.

    Security: Always returns the same message regardless of whether the email
    is registered — prevents user enumeration attacks.

    The reset link is valid for 1 hour and is single-use.
    """
    # Service handles both "found" and "not found" silently
    await initiate_password_reset(data.email, db)

    return MessageResponse(
        message = "If an account with that email exists, "
                  "a password reset link has been sent. "
                  "Please check your inbox (and spam folder)."
    )


# ---------------------------------------------------------------------------
# POST /api/auth/reset-password
# ---------------------------------------------------------------------------

@router.post(
    "/reset-password",
    response_model = MessageResponse,
    summary        = "Complete password reset using a JWT token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db:   AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Validates the reset token and updates the password.

    - Token must be a valid, unexpired JWT signed with JWT_SECRET_KEY.
    - Token purpose must be "password_reset".
    - Token must match the one stored in MongoDB (single-use).
    - Token expires after 1 hour.
    - Password: 8–72 characters (bcrypt limit).
    - On success: token is removed from the database.

    Returns 400 if the token is invalid, expired, or already used.
    """
    await complete_password_reset(data.token, data.password, db)
    return MessageResponse(
        message = "Your password has been reset successfully. You can now sign in."
    )
