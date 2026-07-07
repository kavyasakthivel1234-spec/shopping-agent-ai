"""
app/routes/history_routes.py
-----------------------------
Anonymous history endpoints — no authentication required.

GET    /api/history            — list all history entries (newest first)
DELETE /api/history            — clear all history
DELETE /api/history/{entry_id} — delete a single history entry
POST   /api/history            — save a history entry
"""

import logging
import traceback
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Any

from app.database.mongodb import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["History"])
HISTORY_COLLECTION = "history"


class SaveHistoryRequest(BaseModel):
    query:    str
    type:     str = "shopping"
    response: Any = None


def _serialise(doc: dict) -> dict:
    return {
        "id":        str(doc["_id"]),
        "query":     doc.get("query", ""),
        "type":      doc.get("type", "shopping"),
        "response":  doc.get("response"),
        "createdAt": doc["createdAt"].isoformat()
                     if isinstance(doc.get("createdAt"), datetime) else "",
    }


@router.get("", summary="List all history entries (newest first)")
async def list_history(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        cursor  = db[HISTORY_COLLECTION].find({}).sort("createdAt", -1).limit(100)
        entries = []
        async for doc in cursor:
            entries.append(_serialise(doc))
        return entries
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Save a history entry")
async def save_history(
    body: SaveHistoryRequest,
    db:   AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        doc = {
            "query":     body.query.strip(),
            "type":      body.type,
            "response":  body.response,
            "createdAt": datetime.now(timezone.utc),
        }
        result = await db[HISTORY_COLLECTION].insert_one(doc)
        saved  = await db[HISTORY_COLLECTION].find_one({"_id": result.inserted_id})
        return _serialise(saved)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("", summary="Clear all history")
async def clear_history(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        result = await db[HISTORY_COLLECTION].delete_many({})
        return {"message": f"Cleared {result.deleted_count} history entries."}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{entry_id}", summary="Delete a single history entry")
async def delete_history_entry(
    entry_id: str,
    db:       AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        try:
            obj_id = ObjectId(entry_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid entry ID format.")

        result = await db[HISTORY_COLLECTION].delete_one({"_id": obj_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found.")

        return {"message": "Entry deleted.", "id": entry_id}
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
