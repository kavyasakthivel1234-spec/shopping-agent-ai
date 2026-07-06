"""
main.py
-------
FastAPI application entry point.
"""

import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.database.mongodb import lifespan
from app.routes.auth import router as auth_router
from app.routes.chat_routes import router as chat_router
from app.routes.history_routes import router as history_router
from routes.recommendation_routes import router as recommendation_router
from routes.assistant_routes import router as assistant_router

app = FastAPI(
    title=settings.APP_TITLE,
    description="AI-powered multi-agent shopping assistant with MongoDB authentication",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ==========================
# CORS Configuration
# ==========================

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://shopping-assistant-frontend-bma0.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ==========================
# Routers
# ==========================

app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(recommendation_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")

# ==========================
# Health Check
# ==========================

@app.get("/")
def root():
    return {
        "message": "Shopping Assistant API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "running",
        "version": settings.APP_VERSION,
    }


# ==========================
# Debug Endpoint
# ==========================

@app.get("/api/debug/product-source")
def debug_product_source(q: str = Query(..., description="Search query")):
    from dotenv import load_dotenv
    from services.amazon_service import AmazonService
    from services.local_product_service import LocalProductService

    load_dotenv()

    api_key = os.getenv("SERP_API_KEY", "").strip()

    svc = AmazonService()

    if api_key:
        try:
            result = svc.raw_serpapi_search(q)

            return {
                "query": q,
                "source": "AMAZON_SERPAPI",
                "products_found": result["products_found"],
                "products": result["products"],
            }

        except Exception as e:

            return {
                "query": q,
                "source": "LOCAL_MOCK",
                "products_found": 0,
                "error": str(e),
                "products": [],
            }

    local = LocalProductService()

    requirements = {
        "category": q,
        "budget": 0,
        "features": [],
        "original_query": q,
    }

    products = local.search_products(requirements)

    return {
        "query": q,
        "source": "LOCAL_MOCK",
        "products_found": len(products),
        "products": products[:10],
    }
