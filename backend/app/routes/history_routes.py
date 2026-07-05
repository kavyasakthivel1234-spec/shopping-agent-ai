"""
app/routes/history_routes.py
-----------------------------
MongoDB-backed, user-isolated chat history endpoints.

GET    /api/history            — list current user's history (newest first)
DELETE /api/history            — clear all history for the current user
DELETE /api/history/{entry_id} — delete a single history entry

Schema (collection: "history"):
    {
        _id:       ObjectId,
        userId:    str,          # matches serialise_user(doc)["id"]
        query:     str,          # the user's search text
        type:      str,          # "shopping" | "chat" | "comparison"
        response:  dict,         # full assistant response payload
        createdAt: datetime
    }

All endpoints require Authorization: Bearer <token>.
"""

import logging
import traceback
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Any

from app.database.mongodb import get_database
from app.utils.security   import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])

HISTORY_COLLECTION = "history"


# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------

class SaveHistoryRequest(BaseModel):
    query:    str
    type:     str  = "shopping"   # "shopping" | "chat" | "comparison"
    response: Any  = None         # full assistant response payload


# ---------------------------------------------------------------------------
# Serialiser
# ---------------------------------------------------------------------------

def _serialise(doc: dict) -> dict:
    return {
        "id":        str(doc["_id"]),
        "userId":    str(doc.get("userId", "")),
        "query":     doc.get("query", ""),
        "type":      doc.get("type", "shopping"),
        "response":  doc.get("response"),
        "createdAt": doc["createdAt"].isoformat()
                     if isinstance(doc.get("createdAt"), datetime) else "",
    }


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------

@router.get("", summary="List current user's history (newest first)")
async def list_history(
    request:      Request,
    current_user: dict = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """Returns all history entries for the authenticated user, newest first."""
    try:
        user_id = current_user["id"]
        print(f"[History] Loading history for user_id={user_id}")

        cursor = (
            db[HISTORY_COLLECTION]
            .find({"userId": user_id})
            .sort("createdAt", -1)
            .limit(100)
        )

        entries = []
        async for doc in cursor:
            entries.append(_serialise(doc))

        print(f"[History] Returning {len(entries)} entries")
        return entries

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /api/history   (called by assistant_routes after every response)
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, summary="Save a history entry")
async def save_history(
    body:         SaveHistoryRequest,
    current_user: dict = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """Save one assistant exchange to the user's history."""
    try:
        user_id = current_user["id"]
        now     = datetime.now(timezone.utc)

        doc = {
            "userId":    user_id,
            "query":     body.query.strip(),
            "type":      body.type,
            "response":  body.response,
            "createdAt": now,
        }

        result = await db[HISTORY_COLLECTION].insert_one(doc)
        saved  = await db[HISTORY_COLLECTION].find_one({"_id": result.inserted_id})

        logger.info("[History] Saved entry id=%s user=%s", result.inserted_id, user_id)
        return _serialise(saved)

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# DELETE /api/history   (clear all)
# ---------------------------------------------------------------------------

@router.delete("", summary="Clear all history for the current user")
async def clear_history(
    current_user: dict = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """Permanently deletes all history entries belonging to the current user."""
    try:
        user_id = current_user["id"]
        result  = await db[HISTORY_COLLECTION].delete_many({"userId": user_id})
        logger.info("[History] Cleared %d entries for user=%s", result.deleted_count, user_id)
        return {"message": f"Cleared {result.deleted_count} history entries."}

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# DELETE /api/history/{entry_id}   (single entry)
# ---------------------------------------------------------------------------

@router.delete("/{entry_id}", summary="Delete a single history entry")
async def delete_history_entry(
    entry_id:     str,
    current_user: dict = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """Delete one history entry. Users can only delete their own entries."""
    try:
        user_id = current_user["id"]

        try:
            obj_id = ObjectId(entry_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid entry ID format.")

        result = await db[HISTORY_COLLECTION].delete_one({
            "_id":    obj_id,
            "userId": user_id,
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Entry not found or you do not have permission to delete it.",
            )

        return {"message": "Entry deleted.", "id": entry_id}

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
