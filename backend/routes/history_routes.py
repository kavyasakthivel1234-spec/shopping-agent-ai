"""
history_routes.py
-----------------
Phase 4 — Search history endpoints.

GET    /api/history   → list all saved searches (newest first)
DELETE /api/history   → wipe the entire history

All existing Phase 1–3 endpoints remain untouched.
"""

import traceback
from fastapi import APIRouter, HTTPException
from services.history_service import HistoryService

router = APIRouter()

_history_service: HistoryService | None = None

def _get_history_service() -> HistoryService:
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service


@router.get("/history")
def get_history():
    try:
        return _get_history_service().get_all()
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/history")
def clear_history():
    try:
        _get_history_service().clear()
        return {"message": "History cleared."}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
