"""
app/database/mongodb.py
-----------------------
Async MongoDB connection using Motor.
<<<<<<< HEAD
=======

Key fixes:
  - MONGODB_URI is now read inside connect_to_mongo() (not at module level)
    so Render-injected env vars are always picked up correctly.
  - sys.exit(1) replaced with RuntimeError so FastAPI returns a proper
    503 instead of crashing silently.
  - Full error detail is printed to stdout (visible in Render logs).
>>>>>>> bc38d0f (Fix CORS issue)
"""

import os
import logging
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

<<<<<<< HEAD
# Load environment variables
=======
>>>>>>> bc38d0f (Fix CORS issue)
load_dotenv()

logger = logging.getLogger(__name__)

<<<<<<< HEAD
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = "shopping_assistant"

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
=======
DATABASE_NAME: str = "shopping_assistant"
>>>>>>> bc38d0f (Fix CORS issue)

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """
<<<<<<< HEAD
    Connect to MongoDB Atlas.
=======
    Open the Motor async client and verify the connection with a ping.
    Reads MONGODB_URI at call time so Render env vars are always present.

    Raises:
        RuntimeError: on missing URI or failed connection — FastAPI will
                      return HTTP 503 rather than crashing the process.
>>>>>>> bc38d0f (Fix CORS issue)
    """

    global _client, _database

<<<<<<< HEAD
    if not MONGODB_URI:
        logger.error("[MongoDB] MONGODB_URI is missing.")
        print("[MongoDB] MONGODB_URI is not set.")

        # Don't crash Render
        return
=======
    # Read at call time — never at module import time
    uri = os.getenv("MONGODB_URI", "").strip()

    if not uri:
        msg = (
            "[MongoDB] MONGODB_URI is not set. "
            "Set it in the Render dashboard under Environment Variables."
        )
        logger.critical(msg)
        print(msg)
        raise RuntimeError(msg)
>>>>>>> bc38d0f (Fix CORS issue)

    print(f"[MongoDB] Connecting to Atlas... (URI length={len(uri)})")
    logger.info("[MongoDB] Connecting to Atlas...")

    try:
<<<<<<< HEAD
        _client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000
        )

        _database = _client[DATABASE_NAME]

        # Verify connection
        await _client.admin.command("ping")

        print(f"[MongoDB] Connected successfully (db={DATABASE_NAME})")
        logger.info("[MongoDB] Connected successfully")

    except Exception as exc:

        print(f"[MongoDB] CONNECTION FAILED: {exc}")

        logger.error(
            "[MongoDB] Failed to connect",
            exc_info=True
        )

        print("""
Common causes:
1. Wrong username/password
2. Atlas Network Access missing 0.0.0.0/0
3. Incorrect cluster hostname
4. Password contains special characters (@, #, $, etc.)
5. User lacks readWrite permission
""")

        # IMPORTANT:
        # Don't exit the application
        return


async def close_mongo_connection() -> None:

=======
        _client   = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=15_000)
        _database = _client[DATABASE_NAME]

        await _client.admin.command("ping")

        print(f"[MongoDB] Connected successfully  (db={DATABASE_NAME})")
        logger.info("[MongoDB] Connected to database: %s", DATABASE_NAME)

    except Exception as exc:
        err_str = str(exc)
        print(f"\n[MongoDB] CONNECTION FAILED: {err_str}\n")
        logger.critical("[MongoDB] Failed to connect: %s", exc, exc_info=True)

        # Diagnose common Atlas errors
        if "bad auth" in err_str.lower() or "authentication failed" in err_str.lower():
            print(
                "[MongoDB] FIX: Authentication failed.\n"
                "  → Check MONGODB_URI username and password in Render env vars.\n"
                "  → Special characters in password must be URL-encoded:\n"
                "       @ → %40    # → %23    $ → %24    : → %3A    / → %2F\n"
                "  → Verify the Atlas user exists and has readWrite on 'shopping_assistant'."
            )
        elif "network" in err_str.lower() or "timeout" in err_str.lower():
            print(
                "[MongoDB] FIX: Network/timeout error.\n"
                "  → In Atlas → Network Access, add 0.0.0.0/0 (Allow from anywhere).\n"
                "  → Render's outbound IPs are dynamic — you must allow all IPs."
            )
        elif "ServerSelectionTimeoutError" in err_str:
            print(
                "[MongoDB] FIX: Cannot reach cluster.\n"
                "  → Verify the cluster hostname in MONGODB_URI is correct.\n"
                "  → Check Atlas cluster is not paused (free tier pauses after 60 days idle)."
            )

        raise RuntimeError(f"MongoDB connection failed: {err_str}") from exc


async def close_mongo_connection() -> None:
>>>>>>> bc38d0f (Fix CORS issue)
    global _client

    if _client:
        _client.close()
        logger.info("[MongoDB] Connection closed.")
        print("[MongoDB] Connection closed.")


<<<<<<< HEAD
# ---------------------------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):

=======
@asynccontextmanager
async def lifespan(app):  # noqa: ARG001
>>>>>>> bc38d0f (Fix CORS issue)
    await connect_to_mongo()

    yield

    await close_mongo_connection()


<<<<<<< HEAD
# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_database() -> AsyncIOMotorDatabase:

    if _database is None:
        raise RuntimeError(
            "MongoDB is not connected. "
            "Check MONGODB_URI and Atlas settings."
=======
def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError(
            "MongoDB is not initialised. "
            "The startup connection failed — check Render logs for details."
>>>>>>> bc38d0f (Fix CORS issue)
        )

    return _database
