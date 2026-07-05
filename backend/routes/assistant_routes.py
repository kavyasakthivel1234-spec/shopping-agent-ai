"""
assistant_routes.py
-------------------
POST /api/assistant

Pipeline:
  1. Greeting  → Groq chat response  → { type: "chat", message }
  2. Compare   → ComparisonAgent     → { type: "comparison", data }
  3. Shopping  → Groq extracts filters
               → SerpAPI fetches real Amazon products
               → Recommend & rank
               → ReviewAgent
               → { type: "shopping", data }

After every non-greeting response the exchange is saved to MongoDB
under the authenticated user's history (collection: "history").

Groq = NLP only.  SerpAPI = real products only.  Zero mock data.
"""

import os
import re
import logging
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from agents.orchestrator  import ShoppingAssistantOrchestrator
from agents.intent_router import IntentRouter, GREETING_RESPONSES
from models.product_model import (
    AssistantRequest,
    AssistantResponse,
    Requirements,
    ReviewSummaryResponse,
    ScoredProduct,
)
from app.database.mongodb import get_database
from app.utils.security   import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

HISTORY_COLLECTION = "history"

# Lazy singleton — initialised on first request
_orchestrator: ShoppingAssistantOrchestrator | None = None


def _get_orchestrator() -> ShoppingAssistantOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        print("[Assistant] Initialising orchestrator...")
        print(f"[Assistant] GROQ_API_KEY : {bool(os.getenv('GROQ_API_KEY'))}")
        print(f"[Assistant] SERP_API_KEY : {bool(os.getenv('SERP_API_KEY'))}")
        _orchestrator = ShoppingAssistantOrchestrator()
        print("[Assistant] Orchestrator ready.")
    return _orchestrator


def _safe_scored(data: dict) -> ScoredProduct:
    allowed  = ScoredProduct.model_fields.keys()
    filtered = {k: v for k, v in data.items() if k in allowed}
    filtered.setdefault("id",       "unknown")
    filtered.setdefault("name",     "Unknown Product")
    filtered.setdefault("category", "")
    filtered.setdefault("camera",   "N/A")
    filtered.setdefault("battery",  "N/A")
    filtered.setdefault("score",    0)
    return ScoredProduct(**filtered)


async def _save_to_history(
    db:           AsyncIOMotorDatabase,
    user_id:      str,
    query:        str,
    response_type: str,
    response_payload: dict,
) -> None:
    """
    Persist one assistant exchange to the user's history in MongoDB.
    Non-fatal — exceptions are caught and logged, never surfaced to the user.
    """
    try:
        await db[HISTORY_COLLECTION].insert_one({
            "userId":    user_id,
            "query":     query.strip(),
            "type":      response_type,
            "response":  response_payload,
            "createdAt": datetime.now(timezone.utc),
        })
        print(f"[Assistant] Saved history for user={user_id} type={response_type}")
    except Exception as exc:
        logger.warning("[Assistant] History save failed (non-fatal): %s", exc)


@router.post("/assistant")
async def assistant(
    request:      AssistantRequest,
    current_user: dict                 = Depends(get_current_user),
    db:           AsyncIOMotorDatabase = Depends(get_database),
):
    """POST /api/assistant — main chat + shopping endpoint (JWT protected)."""
    try:
        query   = request.query.strip()
        user_id = current_user["id"]

        if not query:
            raise HTTPException(status_code=400, detail="Query must not be empty.")

        print(f"\n[Assistant] ── New request ─────────────────────────────────")
        print(f"[Assistant] User    : {current_user.get('email') or current_user.get('mobile')}")
        print(f"[Assistant] Query   : {query!r}")

        # ── 1. Greeting fast path ─────────────────────────────────────
        if IntentRouter.is_greeting(query):
            greeting = GREETING_RESPONSES.get(
                re.sub(r"[^\w\s]", "", query).strip().lower()
            ) or GREETING_RESPONSES.get("hi")
            print("[Assistant] Route: greeting")
            return {"type": "chat", "message": greeting}

        # ── 2. Comparison ─────────────────────────────────────────────
        if IntentRouter.is_product_comparison_intent(query):
            print("[Assistant] Route: comparison")
            # Look up last shopping result from MongoDB history
            last_doc = await db[HISTORY_COLLECTION].find_one(
                {"userId": user_id, "type": "shopping"},
                sort=[("createdAt", -1)],
            )
            last_resp = (last_doc or {}).get("response", {})
            top_raw   = last_resp.get("top_pick")
            alt_raw   = last_resp.get("alternatives", [])

            if not top_raw or not alt_raw:
                return {
                    "type":    "chat",
                    "message": "Please search for products first, then I can compare them.",
                }

            orc    = _get_orchestrator()
            result = orc.compare(top_raw["id"], alt_raw[0]["id"])

            if "error" in result:
                raise HTTPException(status_code=502, detail=result["error"])

            payload = {"type": "comparison", "data": result}
            await _save_to_history(db, user_id, query, "comparison", result)
            return payload

        # ── 3. Shopping pipeline ──────────────────────────────────────
        print("[Assistant] Route: shopping pipeline")
        orc    = _get_orchestrator()
        result = orc.process_query(query)

        print(f"[Assistant] Pipeline : {result.get('pipeline')}")

        if "error" in result and "pipeline_type" not in result:
            raise HTTPException(
                status_code=502,
                detail=f"[{result.get('failed_agent','unknown')}] {result['error']}",
            )

        if result.get("pipeline_type") == "smalltalk":
            msg     = result.get("chat_text", "Hello!")
            payload = {"type": "chat", "message": msg}
            await _save_to_history(db, user_id, query, "chat", {"message": msg})
            return payload

        top_pick_raw     = result.get("top_pick")
        alternatives_raw = result.get("alternatives", [])

        if not top_pick_raw:
            print("[Assistant] No products found.")
            msg = (
                f"No matching Amazon products found for \"{query}\". "
                "Please try different keywords or adjust your filters."
            )
            return {"type": "chat", "message": msg}

        # Build Pydantic models
        top_pick     = _safe_scored(top_pick_raw)
        alternatives = [_safe_scored(p) for p in alternatives_raw]

        raw_req = result.get("requirements", {})
        requirements = Requirements(
            category = raw_req.get("category") or raw_req.get("product", ""),
            budget   = float(raw_req.get("budget") or raw_req.get("maxPrice") or 0),
            features = raw_req.get("features", []),
        )

        raw_review     = result.get("review_summary")
        review_summary = ReviewSummaryResponse(**raw_review) if raw_review else None
        confidence     = round(float(result.get("confidence", 0.0)), 2)

        # Log top 3
        print(f"\n[Assistant] Top {min(3, 1+len(alternatives))} products:")
        for i, p in enumerate([top_pick] + alternatives[:2], 1):
            price_str = f"₹{p.price:,.0f}" if p.price else "N/A"
            print(f"  {i}. {p.name} | {price_str} | ★{p.rating or 'N/A'} | {p.brand or 'N/A'}")

        response_data = AssistantResponse(
            requirements   = requirements,
            top_pick       = top_pick,
            alternatives   = alternatives,
            review_summary = review_summary,
            confidence     = confidence,
            pipeline       = result.get("pipeline", []),
        ).model_dump()
        response_data["pipeline_type"] = "shopping"

        # Rich filter chips for the UI
        response_data["filters"] = {
            "product":   raw_req.get("product") or raw_req.get("category", ""),
            "brand":     raw_req.get("brand"),
            "maxPrice":  raw_req.get("maxPrice") or raw_req.get("budget"),
            "minRating": raw_req.get("minRating"),
            "color":     raw_req.get("color"),
            "size":      raw_req.get("size"),
            "storage":   raw_req.get("storage"),
            "ram":       raw_req.get("ram"),
        }

        # ── Persist to MongoDB history ────────────────────────────────
        await _save_to_history(db, user_id, query, "shopping", response_data)

        print("[Assistant] Response sent successfully.")
        return {"type": "shopping", "data": response_data}

    except HTTPException:
        raise
    except Exception as exc:
        print("=" * 72)
        print("[Assistant] UNHANDLED EXCEPTION:")
        print(str(exc))
        traceback.print_exc()
        print("=" * 72)
        raise HTTPException(status_code=500, detail=str(exc))
