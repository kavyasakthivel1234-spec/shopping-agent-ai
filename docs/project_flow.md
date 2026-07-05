# Project Flow

## Overview

The AI Shopping Assistant is a full-stack application that uses Google Gemini to provide
personalised product recommendations and side-by-side product comparisons.

---

## High-Level Architecture

```
┌─────────────────────────────┐
│        React Frontend        │
│  (Vite · port 5173)          │
└────────────┬────────────────┘
             │ HTTP / REST
             ▼
┌─────────────────────────────┐
│      FastAPI Backend         │
│  (Uvicorn · port 8000)       │
│                              │
│  routes/                     │
│  ├─ recommendation_routes    │
│                              │
│  services/                   │
│  ├─ gemini_service           │
│  ├─ recommendation           │
│  └─ comparison               │
│                              │
│  models/                     │
│  └─ product_model            │
│                              │
│  products.json  (data store) │
└────────────┬────────────────┘
             │ Google Generative AI SDK
             ▼
      Google Gemini API
```

---

## Request Flow – Recommendation

1. User types a natural-language query in the React UI.
2. Frontend calls `POST /api/recommendations` with `{ "query": "..." }`.
3. `recommendation_routes.py` delegates to `RecommendationService`.
4. `RecommendationService` loads products from `products.json`.
5. A prompt is constructed and sent to `GeminiService`.
6. Gemini returns a ranked recommendation, which is returned as JSON.
7. Frontend renders the response.

---

## Request Flow – Comparison

1. User selects two or more products to compare.
2. Frontend calls `POST /api/recommendations/compare` with a list of product IDs.
3. `ComparisonService` fetches those products and asks Gemini for a structured comparison.
4. Result is returned as JSON and displayed in a comparison table.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |

Store these in `backend/.env` (excluded from git via `.gitignore`).
