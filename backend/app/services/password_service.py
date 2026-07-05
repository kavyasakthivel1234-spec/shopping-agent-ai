"""
app/services/password_service.py
---------------------------------
Business logic for forgot-password and reset-password flows.

Security principles applied:
  - Email enumeration is prevented: both "email found" and "email not found"
    return the same generic message to the caller.
  - Reset tokens are single-use: cleared from the database after a successful
    reset so they cannot be reused.
  - Old tokens are invalidated when a new reset is requested.
  - Tokens have a 1-hour expiry encoded inside the JWT payload AND stored
    in MongoDB (belt-and-suspenders double check).
  - Passwords are hashed with bcrypt before storage.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

from app.models.user import USERS_COLLECTION
from app.utils.email import send_password_reset_email

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration  (read at call time so .env is already loaded)
# ---------------------------------------------------------------------------

def _secret() -> str:
    return os.getenv("JWT_SECRET_KEY", "change_this_to_a_secure_secret")

def _algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")

RESET_TOKEN_EXPIRE_MINUTES: int = 60   # 1 hour

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

async def initiate_password_reset(email: str, db: AsyncIOMotorDatabase) -> None:
    """
    Start the password reset flow for the given email.

    Always returns without raising — callers respond with a generic message
    regardless of whether the email exists (prevents user enumeration).

    Steps:
      1. Look up the user by email.
      2. If not found — return silently (no error, no hint).
      3. Generate a 1-hour signed JWT reset token.
      4. Store the token + expiry in MongoDB (invalidates any previous token).
      5. Send the reset email.
    """
    email = email.lower().strip()
    user  = await db[USERS_COLLECTION].find_one({"email": email})

    if not user:
        logger.info("[PasswordService] Forgot-password for unknown email: %s", email)
        return   # silent — do not reveal whether the email is registered

    # ── Generate a 1-hour JWT reset token ──────────────────────────
    expire  = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":     email,
        "purpose": "password_reset",   # prevents reuse of login access tokens
        "exp":     expire,
    }
    reset_token = jwt.encode(payload, _secret(), algorithm=_algorithm())

    logger.info("[PasswordService] Reset token generated for: %s (expires in 60 min)", email)

    # ── Store token + expiry in MongoDB (overwrites any previous token) ──
    await db[USERS_COLLECTION].update_one(
        {"email": email},
        {
            "$set": {
                "reset_token":        reset_token,
                "reset_token_expiry": expire,
            }
        },
    )

    # ── Send email ────────────────────────────────────────────────
    try:
        send_password_reset_email(email, reset_token)
        logger.info("[PasswordService] Reset email dispatched to: %s", email)
    except Exception as exc:
        # Log the failure but don't expose it — the generic response is
        # returned regardless.  The reset link is also printed to the
        # server terminal by send_password_reset_email for development use.
        logger.error("[PasswordService] Email send failed for %s: %s", email, exc)


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

async def complete_password_reset(
    token: str, new_password: str, db: AsyncIOMotorDatabase
) -> None:
    """
    Validate the reset token and update the user's password.

    Steps:
      1. Decode and verify the JWT (checks signature + expiry).
      2. Confirm the token's purpose is "password_reset".
      3. Load the user from MongoDB.
      4. Verify the stored token matches (single-use enforcement).
      5. Belt-and-suspenders: check stored expiry in DB.
      6. Hash the new password with bcrypt.
      7. Update the password and remove the reset token fields.

    Raises:
        HTTPException 400: Token is invalid, expired, already used, or
                           purpose field is wrong.
    """
    invalid_token_error = HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail      = "Password reset link is invalid or has expired. "
                      "Please request a new one.",
    )

    # ── Decode + verify JWT signature & expiry ─────────────────────
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_algorithm()])
    except JWTError as exc:
        logger.warning("[PasswordService] Invalid reset token JWT: %s", exc)
        raise invalid_token_error from exc

    # ── Validate purpose field ──────────────────────────────────────
    if payload.get("purpose") != "password_reset":
        logger.warning(
            "[PasswordService] Token purpose mismatch: %s", payload.get("purpose")
        )
        raise invalid_token_error

    email = payload.get("sub", "").lower().strip()
    if not email:
        raise invalid_token_error

    # ── Load user ───────────────────────────────────────────────────
    user = await db[USERS_COLLECTION].find_one({"email": email})
    if not user:
        logger.warning("[PasswordService] No user found for reset email: %s", email)
        raise invalid_token_error

    # ── Single-use check: stored token must match ───────────────────
    stored_token = user.get("reset_token")
    if not stored_token or stored_token != token:
        logger.warning(
            "[PasswordService] Token mismatch or already used for: %s", email
        )
        raise invalid_token_error

    # ── Belt-and-suspenders: DB expiry check ───────────────────────
    stored_expiry: datetime | None = user.get("reset_token_expiry")
    if stored_expiry:
        if stored_expiry.tzinfo is None:
            stored_expiry = stored_expiry.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > stored_expiry:
            logger.warning("[PasswordService] DB expiry passed for: %s", email)
            raise invalid_token_error

    # ── Hash new password ───────────────────────────────────────────
    hashed = _pwd_context.hash(new_password)

    # ── Persist: update password, remove reset fields ───────────────
    await db[USERS_COLLECTION].update_one(
        {"email": email},
        {
            "$set":   {"password": hashed},
            "$unset": {"reset_token": "", "reset_token_expiry": ""},
        },
    )

    logger.info("[PasswordService] Password successfully reset for: %s", email)
