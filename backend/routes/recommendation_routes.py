"""
recommendation_routes.py
------------------------
FastAPI router for all Phase 1 + Phase 2 endpoints.

All business logic lives in the service layer.
This module handles ONLY HTTP concerns.
"""

import traceback
from fastapi import APIRouter, HTTPException

from models.product_model import (
    CompareRequest,
    CompareResponse,
    ComparisonDetail,
    ComparisonResult,
    ProsConsResponse,
    RecommendationRequest,
    RecommendationResponse,
    Requirements,
    ReviewSummaryResponse,
    ScoredProduct,
    Product,
)
from services.gemini_service    import GeminiService
from services.recommendation    import RecommendationService
from services.comparison        import ComparisonService
from services.pros_cons_service import ProsConsService
from services.review_summary    import ReviewSummaryService

router = APIRouter()

# ── Lazy-initialise services to avoid module-level failures ───────────────
_ai_service:             GeminiService          | None = None
_recommendation_service: RecommendationService  | None = None
_comparison_service:     ComparisonService      | None = None
_pros_cons_service:      ProsConsService        | None = None
_review_summary_service: ReviewSummaryService   | None = None


def _get_ai():
    global _ai_service
    if _ai_service is None:
        _ai_service = GeminiService()
    return _ai_service


def _get_recommendation():
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service


def _get_comparison():
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = ComparisonService(_get_ai())
    return _comparison_service


def _get_pros_cons():
    global _pros_cons_service
    if _pros_cons_service is None:
        _pros_cons_service = ProsConsService(_get_ai())
    return _pros_cons_service


def _get_review_summary():
    global _review_summary_service
    if _review_summary_service is None:
        _review_summary_service = ReviewSummaryService(_get_ai())
    return _review_summary_service


# ---------------------------------------------------------------------------
# Error converter — maps service layer exceptions to HTTP responses
# ---------------------------------------------------------------------------
def _raise_for_ai(exc: Exception) -> None:
    """Convert upstream AI exceptions to correct HTTP status codes and re-raise."""
    traceback.print_exc()
    if isinstance(exc, RuntimeError):
        raise HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=502, detail=str(exc))
    raise HTTPException(status_code=500, detail=str(exc))


# ===========================================================================
# Phase 1 — Recommendation
# ===========================================================================

@router.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    """POST /api/recommend — extract requirements via Groq + return scored products."""
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        raw_requirements = _get_ai().extract_requirements(query)
        result           = _get_recommendation().recommend_products(raw_requirements)
    except (RuntimeError, ValueError, Exception) as exc:
        _raise_for_ai(exc)
        return   # unreachable — satisfies static analysers

    requirements = Requirements(**raw_requirements)

    def _safe_scored(data: dict) -> ScoredProduct:
        allowed  = ScoredProduct.model_fields.keys()
        filtered = {k: v for k, v in data.items() if k in allowed}
        return ScoredProduct(**filtered)

    top_pick     = _safe_scored(result["top_pick"]) if result["top_pick"] else None
    alternatives = [_safe_scored(p) for p in result["alternatives"]]

    return RecommendationResponse(
        requirements=requirements,
        top_pick=top_pick,
        alternatives=alternatives,
    )


# ===========================================================================
# Phase 2 — Pros & Cons
# ===========================================================================

@router.get("/pros-cons/{product_id}", response_model=ProsConsResponse)
def get_pros_cons(product_id: str):
    """GET /api/pros-cons/{product_id}"""
    try:
        result = _get_pros_cons().generate_pros_cons(product_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        _raise_for_ai(exc)
        return   # unreachable

    return ProsConsResponse(**result)


# ===========================================================================
# Phase 2 — Comparison
# ===========================================================================

@router.post("/compare", response_model=CompareResponse)
def compare(request: CompareRequest):
    """POST /api/compare"""
    if request.product1_id == request.product2_id:
        raise HTTPException(
            status_code=400,
            detail="product1_id and product2_id must be different.",
        )

    try:
        result = _get_comparison().compare_products(
            request.product1_id, request.product2_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        _raise_for_ai(exc)
        return   # unreachable

    comparison_data = result["comparison"]
    comparison = ComparisonResult(
        camera  = ComparisonDetail(**comparison_data.get("camera",  {"product1": "", "product2": ""})),
        battery = ComparisonDetail(**comparison_data.get("battery", {"product1": "", "product2": ""})),
        price   = ComparisonDetail(**comparison_data.get("price",   {"product1": "", "product2": ""})),
        winner  = comparison_data.get("winner",  ""),
        summary = comparison_data.get("summary", ""),
    )

    def _safe_product(data: dict) -> Product:
        allowed  = Product.model_fields.keys()
        filtered = {k: v for k, v in data.items() if k in allowed}
        return Product(**filtered)

    return CompareResponse(
        product1   = _safe_product(result["product1"]),
        product2   = _safe_product(result["product2"]),
        comparison = comparison,
    )


# ===========================================================================
# Phase 2 — Review Summary
# ===========================================================================

@router.get("/reviews/{product_id}/summary", response_model=ReviewSummaryResponse)
def get_review_summary(product_id: str):
    """GET /api/reviews/{product_id}/summary"""
    try:
        result = _get_review_summary().summarise(product_id)
    except Exception as exc:
        _raise_for_ai(exc)
        return   # unreachable

    return ReviewSummaryResponse(**result)
