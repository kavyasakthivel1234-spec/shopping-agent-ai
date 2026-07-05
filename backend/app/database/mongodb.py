"""
app/database/mongodb.py
-----------------------
Async MongoDB connection using Motor.
"""

import os
import logging
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = "shopping_assistant"

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


# ---------------------------------------------------------------------------
# Connect / disconnect
# ---------------------------------------------------------------------------

async def connect_to_mongo() -> None:
    """
    Connect to MongoDB Atlas.
    """

    global _client, _database

    if not MONGODB_URI:
        logger.error("[MongoDB] MONGODB_URI is missing.")
        print("[MongoDB] MONGODB_URI is not set.")

        # Don't crash Render
        return

    logger.info("[MongoDB] Connecting to Atlas...")

    try:
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

    global _client

    if _client:
        _client.close()
        logger.info("[MongoDB] Connection closed.")
        print("[MongoDB] Connection closed.")


# ---------------------------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):

    await connect_to_mongo()

    yield

    await close_mongo_connection()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_database() -> AsyncIOMotorDatabase:

    if _database is None:
        raise RuntimeError(
            "MongoDB is not connected. "
            "Check MONGODB_URI and Atlas settings."
        )

    return _database
