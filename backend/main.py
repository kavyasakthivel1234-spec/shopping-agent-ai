"""
main.py
-------
FastAPI application entry point.
Authentication removed — all APIs are public.
"""

import os
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config                        import settings
from app.database.mongodb          import lifespan
from app.routes.chat_routes        import router as chat_router
from app.routes.history_routes     import router as history_router
from routes.recommendation_routes  import router as recommendation_router
from routes.assistant_routes       import router as assistant_router

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_cors_from_env: list[str] = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

_cors_always = [
    "https://shopping-assistant-frontend-bma0.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
]

CORS_ORIGINS: list[str] = list(dict.fromkeys(_cors_from_env + _cors_always))
logger.info("[CORS] Allowed origins: %s", CORS_ORIGINS)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title       = settings.APP_TITLE,
    description = "AI-powered shopping assistant — no authentication required",
    version     = settings.APP_VERSION,
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ---------------------------------------------------------------------------
# Routers — all public
# ---------------------------------------------------------------------------
app.include_router(chat_router,           prefix="/api")
app.include_router(history_router,        prefix="/api")
app.include_router(recommendation_router, prefix="/api")
app.include_router(assistant_router,      prefix="/api")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Shopping Assistant API is running", "version": settings.APP_VERSION}


@app.get("/health")
def health_check():
    return {
        "status":       "running",
        "version":      settings.APP_VERSION,
        "cors_origins": CORS_ORIGINS,
    }


# ---------------------------------------------------------------------------
# Debug — verify product source
# ---------------------------------------------------------------------------

@app.get("/api/debug/product-source")
def debug_product_source(q: str = Query(..., description="Search query")):
    from services.amazon_service       import AmazonService
    from services.local_product_service import LocalProductService

    api_key = os.getenv("SERP_API_KEY", "").strip()
    svc     = AmazonService()

    if api_key:
        try:
            result = svc.raw_serpapi_search(q)
            return {
                "query":          q,
                "source":         "AMAZON_SERPAPI" if result["products_found"] > 0 else "LOCAL_MOCK",
                "products_found": result["products_found"],
                "products":       result["products"],
            }
        except Exception as exc:
            return {"query": q, "source": "LOCAL_MOCK", "error": str(exc), "products": []}
    else:
        local_svc     = LocalProductService()
        mock_products = local_svc.search_products(
            {"category": q, "budget": 0, "features": [], "original_query": q}
        )
        return {
            "query":          q,
            "source":         "LOCAL_MOCK",
            "products_found": len(mock_products),
            "products":       mock_products[:10],
        }
