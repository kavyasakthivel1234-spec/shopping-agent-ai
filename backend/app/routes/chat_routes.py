"""
app/routes/chat_routes.py
--------------------------
Anonymous chat session backed by MongoDB.
Auth removed — sessions are stored without userId.

PUT /api/chats/session  — upsert the active session (no auth required)
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.database.mongodb import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["Chats"])
CHATS_COLLECTION = "chats"

ANONYMOUS_USER = "anonymous"


class MessageItem(BaseModel):
    id:   float
    type: str
    text: str = ""
    data: Any = None


class UpsertSessionRequest(BaseModel):
    messages: list[MessageItem]
    title:    str = ""


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
        "userId":    str(doc.get("userId", ANONYMOUS_USER)),
        "title":     doc.get("title", ""),
        "messages":  messages,
        "createdAt": created.isoformat() if isinstance(created, datetime) else "",
        "updatedAt": updated.isoformat() if isinstance(updated, datetime) else "",
    }


@router.put("/session", summary="Upsert the active chat session (no auth required)")
async def upsert_session(
    body: UpsertSessionRequest,
    db:   AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        now = datetime.now(timezone.utc)

        title = body.title
        if not title:
            first_user = next(
                (m for m in body.messages if m.type == "user" and m.text), None
            )
            title = first_user.text[:60] if first_user else "Chat session"

        serialised_messages = [m.model_dump() for m in body.messages]

        result = await db[CHATS_COLLECTION].find_one_and_update(
            {"userId": ANONYMOUS_USER},
            {
                "$set": {
                    "title":     title,
                    "messages":  serialised_messages,
                    "updatedAt": now,
                },
                "$setOnInsert": {
                    "userId":    ANONYMOUS_USER,
                    "createdAt": now,
                },
            },
            upsert          = True,
            return_document = True,
        )

        if result is None:
            result = await db[CHATS_COLLECTION].find_one({"userId": ANONYMOUS_USER})

        saved = _serialise(result)
        logger.info("[ChatRoutes] Session upserted msgs=%d", len(saved["messages"]))
        return saved

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
