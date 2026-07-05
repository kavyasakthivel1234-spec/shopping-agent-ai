"""
app/database/mongodb.py
-----------------------
Async MongoDB connection using Motor.

Loads MONGODB_URI exclusively from the .env file — no credentials are
hardcoded in this file.

Connection flow:
  1. load_dotenv() reads backend/.env
  2. connect_to_mongo() creates an AsyncIOMotorClient from MONGODB_URI
  3. A ping command verifies the connection before the app accepts requests
  4. Prints "MongoDB connected successfully" on success
  5. Raises a descriptive RuntimeError on failure so the server refuses
     to start with a broken database — better to fail fast than to serve
     requests that will all fail.

Usage in routes:
    from app.database.mongodb import get_database
    db = Depends(get_database)
    collection = db["users"]
"""

import os
import logging
import sys
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Load .env before reading any environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — read from .env, never hardcoded
# ---------------------------------------------------------------------------

MONGODB_URI:   str = os.getenv("MONGODB_URI", "")
DATABASE_NAME: str = "shopping_assistant"   # matches the db name in the URI

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_client:   AsyncIOMotorClient   | None = None
_database: AsyncIOMotorDatabase | None = None


# ---------------------------------------------------------------------------
# Connect / disconnect
# ---------------------------------------------------------------------------

async def connect_to_mongo() -> None:
    """
    Open the Motor async client and verify the connection with a ping.

    Raises:
        RuntimeError: If MONGODB_URI is missing from .env.
        Exception:    Any Motor / pymongo error (bad credentials, network, etc.)
                      — the error is logged with detail and the process exits
                      with code 1 so the operator sees the failure immediately.
    """
    global _client, _database

    # ── Guard: URI must be present ──────────────────────────────────
    if not MONGODB_URI:
        msg = (
            "[MongoDB] MONGODB_URI is not set. "
            "Add it to backend/.env and restart the server.\n"
            "Example:\n"
            "  MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxx.mongodb.net/"
            "<dbname>?retryWrites=true&w=majority&appName=Cluster0"
        )
        logger.critical(msg)
        sys.exit(1)

    logger.info("[MongoDB] Connecting to Atlas...")

    try:
        # serverSelectionTimeoutMS limits how long we wait for a server
        _client   = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
        _database = _client[DATABASE_NAME]

        # Ping verifies credentials and network reachability
        await _client.admin.command("ping")

        print(f"[MongoDB] MongoDB connected successfully  (db={DATABASE_NAME})")
        logger.info("[MongoDB] Connected to database: %s", DATABASE_NAME)

    except Exception as exc:
        # Log the full error so the developer knows exactly what went wrong
        print(f"\n[MongoDB] CONNECTION FAILED: {exc}\n", file=sys.stderr)
        logger.critical("[MongoDB] Failed to connect: %s", exc, exc_info=True)

        print(
            "[MongoDB] Common causes:\n"
            "  1. Wrong username or password in MONGODB_URI\n"
            "  2. Your IP is not whitelisted in Atlas Network Access\n"
            "  3. The cluster name / hostname is incorrect\n"
            "  4. Special characters in the password must be URL-encoded\n"
            "     e.g. @ → %40, # → %23, $ → %24\n"
            "  5. Database user does not have readWrite permission\n",
            file=sys.stderr,
        )
        # Exit so the operator is forced to fix the config before retrying
        sys.exit(1)


async def close_mongo_connection() -> None:
    """Close the Motor client gracefully on application shutdown."""
    global _client
    if _client:
        _client.close()
        logger.info("[MongoDB] Connection closed.")
        print("[MongoDB] Connection closed.")


# ---------------------------------------------------------------------------
# FastAPI lifespan context manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):  # noqa: ARG001
    """
    FastAPI lifespan: opens the MongoDB connection on startup and closes
    it when the application shuts down.

    Register in main.py:
        from app.database.mongodb import lifespan
        app = FastAPI(lifespan=lifespan, ...)
    """
    await connect_to_mongo()
    yield
    await close_mongo_connection()


# ---------------------------------------------------------------------------
# FastAPI dependency — inject the database into route handlers
# ---------------------------------------------------------------------------

def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the active Motor database instance.

    Use with FastAPI's Depends():
        @router.post("/signup")
        async def signup(db: AsyncIOMotorDatabase = Depends(get_database)):
            users_col = db["users"]
            ...

    Raises:
        RuntimeError: If called before connect_to_mongo() has succeeded.
    """
    if _database is None:
        raise RuntimeError(
            "MongoDB database is not initialised. "
            "Ensure 'lifespan' is registered in the FastAPI app definition."
        )
    return _database
