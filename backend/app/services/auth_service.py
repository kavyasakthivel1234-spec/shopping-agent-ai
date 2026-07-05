"""
app/services/auth_service.py
-----------------------------
Business logic for user authentication.
No OTP — direct signup with name / email / mobile / password.
"""

import logging

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

from app.models.user    import USERS_COLLECTION, build_user_document, serialise_user
from app.schemas.auth   import UserCreate, UserLogin
from app.utils.security import create_access_token

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of a plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored hash."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

async def signup_user(data: UserCreate, db: AsyncIOMotorDatabase) -> dict:
    """
    Register a new user directly — no OTP required.

    Steps:
      1. Normalise email + mobile.
      2. Check email uniqueness.
      3. Check mobile uniqueness.
      4. Hash password with bcrypt.
      5. Insert document into MongoDB.
      6. Return serialised user dict (no password).

    Raises:
        409 — email or mobile already registered.
        500 — database insertion failed.
    """
    email  = data.email.lower().strip()
    mobile = data.mobile.strip()

    # ── Uniqueness checks ──────────────────────────────────────────
    if await db[USERS_COLLECTION].find_one({"email": email}):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail      = "An account with this email address already exists.",
        )
    if await db[USERS_COLLECTION].find_one({"mobile": mobile}):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail      = "An account with this mobile number already exists.",
        )

    # ── Hash and insert ────────────────────────────────────────────
    hashed = hash_password(data.password)
    doc    = build_user_document(
        name            = data.name,
        email           = email,
        hashed_password = hashed,
        mobile          = mobile,
    )

    result = await db[USERS_COLLECTION].insert_one(doc)
    if not result.inserted_id:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = "Failed to create user account. Please try again.",
        )

    created_doc = await db[USERS_COLLECTION].find_one({"_id": result.inserted_id})
    logger.info("[AuthService] New user registered: %s / %s", email, mobile)
    return serialise_user(created_doc)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def login_user(data: UserLogin, db: AsyncIOMotorDatabase) -> dict:
    """
    Authenticate by email or mobile + password.

    Raises:
        400 — neither email nor mobile provided.
        401 — invalid credentials.
    """
    invalid_creds = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Invalid credentials. Please check your email/mobile and password.",
        headers     = {"WWW-Authenticate": "Bearer"},
    )

    # Build lookup query
    if data.email:
        query = {"email": data.email.lower().strip()}
    elif data.mobile:
        query = {"mobile": data.mobile.strip()}
    else:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail      = "Provide either email or mobile number.",
        )

    user_doc = await db[USERS_COLLECTION].find_one(query)
    if not user_doc:
        raise invalid_creds

    if not verify_password(data.password, user_doc["password"]):
        raise invalid_creds

    subject = user_doc.get("email") or user_doc.get("mobile", "")
    token   = create_access_token(data={"sub": subject})
    user    = serialise_user(user_doc)

    logger.info("[AuthService] User logged in: %s", subject)
    return {"access_token": token, "token_type": "bearer", "user": user}
