"""
app/utils/security.py
---------------------
JWT creation, verification, and FastAPI dependency for protected routes.

FIX 1: JWT_SECRET_KEY, JWT_ALGORITHM are now read inside each function
        (not at module import time) so they always pick up the real .env
        values regardless of import order.

FIX 2: get_current_user now looks up the user by EITHER email OR mobile
        because login_user() sets sub = email OR mobile depending on which
        field the user logged in with.  Previously only email lookup was done,
        causing 401 for users who signed in with their mobile number.
"""

import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.models.user      import USERS_COLLECTION, serialise_user

logger = logging.getLogger(__name__)

# OAuth2 scheme — FastAPI uses this to extract the Bearer token from the
# Authorization header and surface a 401 when it is absent.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Helpers to read config at call time (not import time)
# ---------------------------------------------------------------------------

def _secret() -> str:
    return os.getenv("JWT_SECRET_KEY", "change_this_to_a_secure_secret")

def _algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")

def _expire_days() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT.
    Payload must include { "sub": user_email_or_mobile }.
    """
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(days=_expire_days())
    )
    to_encode["exp"] = expire
    token = jwt.encode(to_encode, _secret(), algorithm=_algorithm())
    logger.debug("[Security] JWT created for sub=%s", data.get("sub"))
    return token


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT.

    Raises:
        HTTPException 401 — invalid, expired, or missing 'sub'.
    """
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail      = "Could not validate credentials. Token is invalid or expired.",
        headers     = {"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_algorithm()])
        print(f"[Security] Decoded JWT payload: sub={payload.get('sub')}")
        subject: str = payload.get("sub")
        if not subject:
            logger.warning("[Security] JWT missing 'sub' field")
            raise credentials_exception
        return payload
    except JWTError as exc:
        logger.warning("[Security] JWT verification failed: %s", exc)
        raise credentials_exception from exc


# ---------------------------------------------------------------------------
# FastAPI dependency — resolve authenticated user
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """
    Extract + validate the Bearer token, then load the user from MongoDB.

    The JWT 'sub' field is set to the user's EMAIL when they log in with email,
    or their MOBILE number when they log in with mobile.

    This function tries BOTH lookups so either login method works correctly
    with all protected endpoints (including /api/chats).

    Raises 401 if:
      - Token is missing / invalid / expired
      - The user no longer exists in MongoDB
    """
    print(f"[Security] get_current_user called — token present: {bool(token)}")

    payload = verify_token(token)
    subject = payload.get("sub")   # email OR mobile number

    print(f"[Security] Looking up user by sub={subject!r}")

    # Try email first, then mobile — sub is whichever field was used to log in
    user_doc = await db[USERS_COLLECTION].find_one({"email": subject})
    if user_doc is None:
        user_doc = await db[USERS_COLLECTION].find_one({"mobile": subject})

    if user_doc is None:
        logger.warning("[Security] User not found for sub=%s", subject)
        print(f"[Security] LOOKUP FAILED for sub={subject!r} — token is stale, user must re-login")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Session expired. Please log out and log back in.",
            headers     = {"WWW-Authenticate": "Bearer"},
        )

    print(f"[Security] Authenticated: email={user_doc.get('email')} mobile={user_doc.get('mobile')}")
    return serialise_user(user_doc)
