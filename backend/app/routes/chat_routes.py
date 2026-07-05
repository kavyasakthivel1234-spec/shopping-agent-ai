"""
app/routes/chat_routes.py
--------------------------
User-isolated chat session backed by MongoDB.

One session per user — upsert model:
  PUT /api/chats/session  — upsert (create or fully replace) the session

All endpoints require Authorization: Bearer <token>.
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.database.mongodb import get_database
from app.utils.security   import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Chats"])

CHATS_COLLECTION = "chats"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MessageItem(BaseModel):
    id:   float
    type: str
    text: str = ""
    data: Any = None   # shopping / comparison payload — arbitrary nested structure


class UpsertSessionRequest(BaseModel):
    messages: list[MessageItem]
    title:    str = ""


# ---------------------------------------------------------------------------
# Serialiser
# ---------------------------------------------------------------------------

def _serialise(doc: dict) -> dict:
    messages = []
    for m in doc.get("messages", []):
        messages.append({
            "id":   m.get("id", 0),
            "type": m.get("type", ""),
            "text": m.get("text", ""),
            "data": m.get("data") or {},
        })
    created = doc.get("createdAt")
    updated = doc.get("updatedAt")
    return {
        "id":        str(doc["_id"]),
        "userId":    str(doc.get("userId", "")),
        "title":     doc.get("title", ""),
        "messages":  messages,
        "createdAt": created.isoformat() if isinstance(created, datetime) else "",
        "updatedAt": updated.isoformat() if isinstance(updated, datetime) else "",
    }


# ---------------------------------------------------------------------------
# PUT /api/chats/session  — upsert the one active session for this user
# ---------------------------------------------------------------------------

@router.put(
    "/session",
    summary="Upsert (create or replace) the current user's chat session",
)
async def upsert_session(
    body:         UpsertSessionRequest,
    current_user: dict = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create the session if it doesn't exist, or fully replace the messages
    if it does.  One document per user — no accumulating stale sessions.

    Returns the saved session.
    """
    try:
        user_id = str(current_user.get("id") or current_user.get("_id", ""))
        now     = datetime.now(timezone.utc)

        # Derive title from first user message
        title = body.title
        if not title:
            first_user = next(
                (m for m in body.messages if m.type == "user" and m.text), None
            )
            title = first_user.text[:60] if first_user else "Chat session"

        serialised_messages = [m.model_dump() for m in body.messages]

        result = await db[CHATS_COLLECTION].find_one_and_update(
            {"userId": user_id},
            {
                "$set": {
                    "title":     title,
                    "messages":  serialised_messages,
                    "updatedAt": now,
                },
                "$setOnInsert": {
                    "createdAt": now,
                },
            },
            upsert          = True,
            return_document = True,
        )

        # Motor returns None on some driver versions when upserting a new doc
        if result is None:
            result = await db[CHATS_COLLECTION].find_one({"userId": user_id})

        saved = _serialise(result)
        logger.info(
            "[ChatRoutes] Session upserted id=%s msgs=%d",
            saved["id"],
            len(saved["messages"]),
        )
        return saved

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[ChatRoutes] PUT /api/chats/session failed: %s", exc, exc_info=True
        )
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
