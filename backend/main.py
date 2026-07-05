"""
main.py
-------
FastAPI application entry point.

Routers:
  /api/auth/*          — signup, login, profile, forgot/reset password
  /api/chats/session   — PUT: upsert user chat session (MongoDB)
  /api/history/*       — user-isolated search history (MongoDB, JWT-protected)
  /api/recommend       — Phase 1 + 2 recommendation endpoints
  /api/assistant       — Phase 3 multi-agent assistant
  /api/debug/*         — debug / audit endpoints
"""

import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config                       import settings
from app.database.mongodb         import lifespan
from app.routes.auth              import router as auth_router
from app.routes.chat_routes       import router as chat_router
from app.routes.history_routes    import router as history_router      # MongoDB history
from routes.recommendation_routes import router as recommendation_router
from routes.assistant_routes      import router as assistant_router

app = FastAPI(
    title       = settings.APP_TITLE,
    description = "AI-powered multi-agent shopping assistant with MongoDB authentication",
    version     = settings.APP_VERSION,
    lifespan    = lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router,            prefix="/api")   # /api/auth/*
app.include_router(chat_router,            prefix="/api")   # /api/chats/*
app.include_router(history_router,         prefix="/api")   # /api/history/* (MongoDB)
app.include_router(recommendation_router,  prefix="/api")   # /api/recommend, etc.
app.include_router(assistant_router,       prefix="/api")   # /api/assistant

# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Liveness probe — returns HTTP 200 when the server is up."""
    return {"status": "running", "version": settings.APP_VERSION}


# ---------------------------------------------------------------------------
# Debug endpoint — verify product source without Gemini processing
# ---------------------------------------------------------------------------

@app.get("/api/debug/product-source")
def debug_product_source(q: str = Query(..., description="Search query")):
    """
    GET /api/debug/product-source?q=<query>

    Returns raw Amazon products (SerpAPI if key is set, otherwise mock)
    WITHOUT any Gemini processing.
    """
    from services.amazon_service import AmazonService
    from dotenv import load_dotenv
    load_dotenv()

    api_key    = os.getenv("SERP_API_KEY", "").strip()
    key_status = "SET" if api_key else "NOT SET"
    svc        = AmazonService()

    if api_key:
        try:
            result = svc.raw_serpapi_search(q)
            return {
                "query":          q,
                "serp_api_key":   key_status,
                "source":         "AMAZON_SERPAPI" if result["products_found"] > 0 else "LOCAL_MOCK",
                "products_found": result["products_found"],
                "products":       result["products"],
            }
        except Exception as exc:
            return {
                "query":          q,
                "serp_api_key":   key_status,
                "source":         "LOCAL_MOCK",
                "products_found": 0,
                "error":          str(exc),
                "products":       [],
            }
    else:
        requirements  = {"category": q, "budget": 0, "features": [], "original_query": q}
        mock_products = svc._search_local_catalogue(requirements)
        return {
            "query":          q,
            "serp_api_key":   key_status,
            "source":         "LOCAL_MOCK",
            "products_found": len(mock_products),
            "reason":         "SERP_API_KEY is not set in .env.",
            "how_to_fix":     "1. Get a free key at https://serpapi.com  2. Add SERP_API_KEY=your_key to backend/.env  3. Restart.",
            "products":       mock_products[:10],
        }
