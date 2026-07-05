# AI Shopping Assistant Agent — Complete Project Documentation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Architecture & Multi-Agent Pipeline](#4-architecture--multi-agent-pipeline)
5. [Backend — Services Layer](#5-backend--services-layer)
6. [Backend — Agents Layer](#6-backend--agents-layer)
7. [Backend — Routes (API Endpoints)](#7-backend--routes-api-endpoints)
8. [Backend — Models](#8-backend--models)
9. [Backend — Configuration](#9-backend--configuration)
10. [Frontend — Pages](#10-frontend--pages)
11. [Frontend — Components](#11-frontend--components)
12. [Frontend — API Service](#12-frontend--api-service)
13. [Data Storage](#13-data-storage)
14. [Environment Variables](#14-environment-variables)
15. [Setup & Running Locally](#15-setup--running-locally)
16. [API Reference](#16-api-reference)
17. [Hybrid Search Architecture](#17-hybrid-search-architecture)
18. [Intent Routing System](#18-intent-routing-system)
19. [Deployment](#19-deployment)
20. [Development Phases Summary](#20-development-phases-summary)

---

## 1. Project Overview

The **AI Shopping Assistant Agent** is a full-stack, multi-agent AI automation system
that helps users discover, compare, and evaluate products using natural language.

**Key capabilities:**
- Natural language product search ("smartphone under 20000 with good camera")
- Multi-source product aggregation (Amazon via SerpAPI or local dataset, Flipkart)
- AI-powered recommendations ranked by relevance score and user rating
- Side-by-side product comparison with AI-generated winner declaration
- AI pros and cons for any product
- Review summarisation (liked / disliked topics)
- Full conversational chat interface backed by Llama 3 on Groq
- Favourites and persistent search history
- Dark-theme premium UI

**AI model:** Llama 3.3 70B Versatile via Groq API (free tier available)
**No web scraping.** Product data comes from structured catalogues and optional SerpAPI.

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| AI LLM | Llama 3.3 70B via Groq | groq==1.5.0 |
| Backend | FastAPI + Uvicorn | fastapi==0.115.5 |
| Backend validation | Pydantic v2 | pydantic==2.10.3 |
| Backend env | python-dotenv | 1.0.1 |
| Frontend | React 18 | 18.3.1 |
| Frontend build | Vite 5 | 5.3.4 |
| Frontend HTTP | Fetch API | native |
| Python | 3.11+ | 3.13 confirmed |
| Node.js | 18+ | 22.19.0 confirmed |

---

## 3. Project Structure

```
shopping-assistant-agent/
│
├── backend/
│   ├── agents/                    # Multi-agent layer
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Central pipeline coordinator
│   │   ├── intent_router.py       # Routes: greeting / shopping / general
│   │   ├── requirement_agent.py   # Extracts category, budget, features
│   │   ├── amazon_search_agent.py # Fetches Amazon products
│   │   ├── flipkart_search_agent.py # Fetches Flipkart products
│   │   ├── recommendation_agent.py # Scores and ranks merged pool
│   │   ├── review_agent.py        # Summarises product reviews
│   │   └── comparison_agent.py    # Side-by-side comparison
│   │
│   ├── services/                  # Business logic & data access
│   │   ├── gemini_service.py      # Groq/Llama3 AI wrapper
│   │   ├── local_product_service.py # Reads products.json
│   │   ├── amazon_service.py      # SerpAPI + local fallback
│   │   ├── flipkart_service.py    # Flipkart catalogue
│   │   ├── recommendation.py      # Core scoring engine
│   │   ├── comparison.py          # Cross-source comparison
│   │   ├── pros_cons_service.py   # AI pros/cons generation
│   │   ├── review_summary.py      # AI review summarisation
│   │   ├── history_service.py     # JSON-based search history
│   │   └── favorite_service.py    # JSON-based favourites
│   │
│   ├── routes/                    # FastAPI routers
│   │   ├── assistant_routes.py    # POST /api/assistant
│   │   ├── recommendation_routes.py # POST /api/recommend + others
│   │   ├── history_routes.py      # GET/DELETE /api/history
│   │   └── favorite_routes.py     # CRUD /api/favorites
│   │
│   ├── models/
│   │   └── product_model.py       # All Pydantic request/response models
│   │
│   ├── data/
│   │   ├── search_history.json    # Persistent search history
│   │   └── favorites.json         # Persistent favourites
│   │
│   ├── app.py                     # FastAPI app entry point
│   ├── config.py                  # Environment-based settings
│   ├── products.json              # Local product catalogue
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Local secrets (git-ignored)
│   └── .env.example               # Template for new developers
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatAssistant.jsx  # Full chat interface
│   │   │   ├── ProductCard.jsx    # Product with source badge
│   │   │   ├── RecommendationList.jsx
│   │   │   ├── ComparisonCard.jsx
│   │   │   ├── ProsConsCard.jsx
│   │   │   ├── ReviewSummaryCard.jsx
│   │   │   ├── RequirementsCard.jsx
│   │   │   └── SearchBar.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── HomePage.jsx       # Search-based recommendations
│   │   │   ├── AssistantPage.jsx  # Chat interface wrapper
│   │   │   ├── FavoritesPage.jsx  # Saved products
│   │   │   └── HistoryPage.jsx    # Past searches
│   │   │
│   │   ├── services/
│   │   │   └── api.js             # All fetch calls to backend
│   │   │
│   │   ├── App.jsx                # Tab navigation + dark mode toggle
│   │   ├── App.css                # Premium dark theme
│   │   └── main.jsx               # React entry point
│   │
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── .env.example
│   └── vercel.json
│
├── docs/
│   ├── DOCUMENTATION.md           # This file
│   ├── ai_automation_flow.md      # Agent pipeline diagram
│   └── project_flow.md            # Request flow documentation
│
├── render.yaml                    # Render.com deployment config
├── README.md
└── .gitignore
```

---

## 4. Architecture & Multi-Agent Pipeline

### Pipeline Flow

```
User Input (natural language)
        │
        ▼
  IntentRouter
  ┌─────────────────────────────────────────────┐
  │  is_greeting?  →  SmallTalkHandler          │
  │  is_shopping?  →  Shopping Pipeline         │
  │  else          →  General Chat (Llama 3)    │
  └─────────────────────────────────────────────┘
        │ [shopping path]
        ▼
  RequirementAgent
  (Groq LLM → extract category, budget, features)
  (Fallback: rule-based regex extraction)
        │
        ├──────────────────────────────┐
        ▼                              ▼
  AmazonSearchAgent           FlipkartSearchAgent
  (SerpAPI if key set,        (Flipkart static
   else local catalogue)       catalogue)
        │                              │
        └──────────┬───────────────────┘
                   ▼
           Merge & Deduplicate
           (Amazon + Flipkart pool)
                   │
                   ▼
        RecommendationAgent
        (Filter by category + budget)
        (Score by features + rating)
        (Split: top_pick + alternatives)
                   │
                   ▼
           ReviewAgent (non-fatal)
           (Summarise mock reviews)
           (liked[] + disliked[])
                   │
                   ▼
           Final Response
  {
    requirements, top_pick, alternatives,
    review_summary, confidence, pipeline
  }
```

### Agent Contracts

Every agent follows the same result envelope:

```python
# Success
{ "agent": "AgentName", "status": "success", "data": {...} }

# Error
{ "agent": "AgentName", "status": "error", "error": "message" }
```

The orchestrator checks `status` at each step. `RequirementAgent` and
`RecommendationAgent` failures halt the pipeline. `ReviewAgent` failure
is non-fatal — the response continues without review data.

---

## 5. Backend — Services Layer

### `gemini_service.py` — AI Wrapper (Groq + Llama 3)

Despite the filename, this service uses **Groq** internally.
The class name `GeminiService` is kept for backwards compatibility so no
agent or route needs to change.

| Method | Purpose | Returns |
|--------|---------|---------|
| `extract_requirements(query)` | LLM + rule fallback: parse natural language into structured requirements | `{category, budget, features}` |
| `generate_pros_cons(product)` | Generate 2-4 pros and 2-4 cons for a product | `{pros[], cons[]}` |
| `generate_comparison(p1, p2)` | AI side-by-side comparison with winner | `{camera, battery, price, winner, summary}` |
| `summarise_reviews(reviews[])` | Extract liked/disliked topics from review text | `{liked[], disliked[]}` |
| `chat_response(message)` | Friendly reply to greetings | `str` |
| `chat(query)` | General chat for non-shopping queries | `str` |
| `is_smalltalk(query)` | Static method: detect greetings | `bool` |

**Fallback extraction** — if the LLM fails or returns an empty category,
`_rule_extract_requirements()` uses regex patterns to parse:
- Budget: `under ₹20000`, `below 20k`, `20000 rupees`, bare 4-6 digit numbers
- Category: keyword matching against alias map
- Features: keyword scan for camera, battery, 5g, fast charging, display

---

### `local_product_service.py` — Local Product Reader

Reads `products.json` and tags every product with `source="Amazon"`,
`source_type="Local"`. Used as the fallback inside `AmazonService`.

---

### `amazon_service.py` — Hybrid Amazon Search

**Decision logic:**
```
SERP_API_KEY present?
    YES → try SerpAPI (real Amazon.in results)
          success  → return products (source_type="Real")
          failure  → fall back to local catalogue
    NO  → use local catalogue (source_type="Local")
```

Startup log printed to console:
- `[AmazonService] SERP_API_KEY found — will attempt SerpAPI first`
- `[AmazonService] No SERP_API_KEY — using Local Products Fallback`

The built-in `AMAZON_CATALOGUE` (13 products across 5 categories) is used
as the primary local fallback, merged with `products.json` results.

---

### `flipkart_service.py` — Flipkart Catalogue

Static catalogue of 13 products across smartphones, laptops, headphones,
smartwatches, and tablets. All tagged `source="Flipkart"`.

Replace `_fetch_products()` with a real Flipkart Affiliate API call
without touching any agent code.

---

### `recommendation.py` — Scoring Engine

Accepts an optional `product_pool` parameter. If omitted, falls back to
`products.json` (backwards-compatible with `/api/recommend`).

**Scoring rules:**

| Condition | Points |
|-----------|--------|
| Camera ≥ 50 MP or "good camera" keyword | +10 |
| Battery ≥ 5000 mAh | +10 |
| Fast charging keyword | +5 |
| 5G in product name | +5 |
| Rating > 4.0 | +(rating - 4.0) × 20, max ~8 |

---

### `comparison.py` — Cross-Source Comparison

Builds a unified catalogue from `products.json`, `AMAZON_CATALOGUE`, and
`FLIPKART_CATALOGUE`. Enables comparing an Amazon product against a
Flipkart product by product ID.

---

### `history_service.py` — Search History

Thread-safe JSON file storage. Stores per-search:
`timestamp`, `query`, `top_pick` (id, name, price), `alternatives[]`,
`confidence`, `assistant_response`

Capped at 100 entries (oldest dropped).

---

### `favorite_service.py` — Favourites

Thread-safe JSON file storage. Add is idempotent (no duplicates).
Supports add, list, remove by product ID.

---

### `pros_cons_service.py` — Pros & Cons

Looks up a product by ID from `products.json`, then calls
`GeminiService.generate_pros_cons()`.

---

### `review_summary.py` — Review Summarisation

Holds a static `MOCK_REVIEWS` dict keyed by product ID (sp-001 through
sp-008). Falls back to generic reviews for unknown IDs. Passes reviews to
`GeminiService.summarise_reviews()`.

---

## 6. Backend — Agents Layer

### `orchestrator.py` — ShoppingAssistantOrchestrator

Central coordinator. All services are injected via constructor parameters
(defaulting to real instances). This makes the orchestrator fully testable
with mock services.

**Key methods:**
- `process_query(query)` — full pipeline or smalltalk shortcut
- `compare(product1_id, product2_id)` — standalone comparison sub-pipeline

---

### `intent_router.py` — IntentRouter

Static utility class for query classification.

| Method | Logic |
|--------|-------|
| `is_greeting(query)` | Exact phrase match: hi, hello, hey, good morning, how are you, etc. |
| `is_shopping_query(query)` | Keyword match: phone, laptop, earbuds, budget patterns, "best X", "recommend a X" |
| `is_product_comparison_intent(query)` | "compare"/"vs" + product entity reference |
| `is_general_chat(query)` | Neither greeting nor shopping |

`GREETING_RESPONSES` is a dict of pre-written replies for common greetings,
used in `assistant_routes.py` to avoid an unnecessary LLM call for simple greetings.

---

### `requirement_agent.py` — RequirementAgent

Wraps `GeminiService.extract_requirements()`. Validates input, logs result,
and returns the normalised requirements dict.

**Output:**
```json
{ "category": "smartphone", "budget": 20000.0, "features": ["good camera"] }
```

---

### `amazon_search_agent.py` — AmazonSearchAgent

Wraps `AmazonService.search_products()`. Returns agent envelope with a
list of products tagged `source="Amazon"`.

---

### `flipkart_search_agent.py` — FlipkartSearchAgent

Wraps `FlipkartService.search_products()`. Returns agent envelope with a
list of products tagged `source="Flipkart"`.

---

### `recommendation_agent.py` — RecommendationAgent

Accepts the merged product pool via `run(requirements, product_pool=...)`.
Calls `RecommendationService.recommend_products()` and calculates confidence:

```
base        = top_pick.score / 30
depth_bonus = min(len(alternatives) × 0.04, 0.20)
confidence  = clamp(base + depth_bonus, 0.0, 1.0)
# If score=0 but products exist: base = 0.50
```

---

### `review_agent.py` — ReviewAgent

Calls `ReviewSummaryService.summarise(product_id)`. Failure is **non-fatal** —
the orchestrator continues without review data if this agent errors.

---

### `comparison_agent.py` — ComparisonAgent

Calls `ComparisonService.compare_products(id1, id2)`. Guards against
comparing a product with itself (returns error immediately).

---

## 7. Backend — Routes (API Endpoints)

### `assistant_routes.py`

**POST /api/assistant**

The primary endpoint. Routes through IntentRouter before deciding path:

| Intent | Handler | Response shape |
|--------|---------|---------------|
| Greeting | Pre-written response dict | `{type:"chat", message:"..."}` |
| Product comparison intent | Orchestrator comparison pipeline | `{type:"comparison", data:{...}}` |
| Shopping query | Full orchestrator pipeline | `{type:"shopping", data:{...}}` |
| General chat | `GeminiService.chat()` | `{type:"chat", message:"..."}` |

---

### `recommendation_routes.py`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/recommend` | Extract requirements + return scored products from local catalogue |
| GET | `/api/pros-cons/{product_id}` | AI pros and cons |
| POST | `/api/compare` | AI side-by-side comparison |
| GET | `/api/reviews/{product_id}/summary` | Review summarisation |

---

### `history_routes.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/history` | Return all history (newest first) |
| DELETE | `/api/history` | Clear all history |

---

### `favorite_routes.py`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/favorites` | Add product to favourites (idempotent) |
| GET | `/api/favorites` | List all favourited products |
| DELETE | `/api/favorites/{product_id}` | Remove from favourites |

---

### Core endpoint

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe: `{"status":"running","version":"4.0.0"}` |

---

## 8. Backend — Models

All Pydantic models live in `models/product_model.py`.

### `Product`
```python
id, name, price, category, camera, battery,
source="Local", source_type="Local", brand="", rating=0.0,
link="", thumbnail=""
```

### `ScoredProduct` (extends Product fields)
Adds `score: int`.

### `Requirements`
```python
category: str, budget: float, features: list[str]
```

### `AssistantRequest` / `AssistantResponse`
Request: `{ query: str }`
Response: `{ requirements, top_pick, alternatives, review_summary, confidence, pipeline }`

### `RecommendationResponse`
`{ requirements, top_pick, alternatives }`

### `CompareResponse`
`{ product1, product2, comparison: { camera, battery, price, winner, summary } }`

### `ReviewSummaryResponse`
`{ product_id, review_count, liked[], disliked[] }`

### `ProsConsResponse`
`{ product_id, product_name, pros[], cons[] }`

---

## 9. Backend — Configuration

### `config.py`

All `os.getenv()` calls happen inside `__init__` (not at class-body time)
so they run after `load_dotenv()` has populated the environment.

```python
from config import settings

settings.GROQ_API_KEY        # str
settings.ALLOWED_ORIGINS     # list[str]
settings.PRODUCTS_PATH       # Path
settings.SEARCH_HISTORY_PATH # Path
settings.FAVORITES_PATH      # Path
settings.DEBUG               # bool
settings.HOST                # str
settings.PORT                # int
```

### `app.py`

Entry point. Registers all four routers under `/api` prefix.
CORS middleware uses `settings.ALLOWED_ORIGINS`.

---

## 10. Frontend — Pages

### `HomePage.jsx`
Search-based recommendations. Uses `getRecommendations()` via the
`/api/recommend` endpoint. Shows `RequirementsCard`, `RecommendationList`
with comparison slots, and `ComparisonCard`.

### `AssistantPage.jsx`
Thin wrapper around `ChatAssistant`. Handles the AI Assistant tab.

### `FavoritesPage.jsx`
Fetches from `/api/favorites` on mount. Remove button calls
`DELETE /api/favorites/{id}`.

### `HistoryPage.jsx`
Fetches from `/api/history` on mount. Displays:
- Timestamp (formatted to en-IN locale)
- User query
- Top pick (name + price)
- Alternatives (up to 3 names)
- Confidence percentage
- Assistant response summary

Clear All calls `DELETE /api/history`.

---

## 11. Frontend — Components

### `ChatAssistant.jsx`
The main chat interface. Handles three response types from the backend:

| `data.type` | Rendered as |
|-------------|-------------|
| `"chat"` | `PlainTextBubble` — plain text left-aligned |
| `"shopping"` | `ShoppingBubble` — rich product cards |
| `"comparison"` | `ComparisonCard` embedded in a bubble |

**Conversation memory:** Last 3 shopping turns are summarised into a
context prefix appended to the next query before sending to the backend.

**Source label in `ProductMini`:** Shows `"Amazon | Real"` or
`"Amazon | Local"` based on `source_type`.

---

### `ProductCard.jsx`
Full product card used in `RecommendationList`. Includes:
- `SourceBadge` — `"Amazon | Real Product"` or `"Amazon | Local Dataset"`
  with a coloured dot indicator
- Compare button (slots into RecommendationList state)
- Save button (calls `POST /api/favorites`)
- Lazy `ProsConsCard` accordion
- Lazy `ReviewSummaryCard` accordion

---

### `RecommendationList.jsx`
Manages the compare-slot state machine:
1. User presses Compare on product A → stored in slot 0
2. User presses Compare on product B → stored in slot 1
3. Both slots filled → auto-triggers `POST /api/compare`
4. `ComparisonCard` renders with AI result

---

### `ComparisonCard.jsx`
Table-based side-by-side comparison. Shows:
camera, battery, price rows + winner banner + AI summary.

---

### `ProsConsCard.jsx` / `ReviewSummaryCard.jsx`
Lazy-loading accordions. First open fetches from the API and caches
the result; subsequent toggles reuse cached data.

---

### `SearchBar.jsx` / `RequirementsCard.jsx`
Simple controlled form and display-only card used in `HomePage`.

---

## 12. Frontend — API Service

`src/services/api.js` exports all fetch functions.

```js
// Phase 1
getRecommendations(query)       // POST /api/recommend

// Phase 2
getProsAndCons(productId)       // GET  /api/pros-cons/{id}
compareProducts(id1, id2)       // POST /api/compare
getReviewSummary(productId)     // GET  /api/reviews/{id}/summary

// Phase 3
runAssistant(query)             // POST /api/assistant

// Phase 4
getHistory()                    // GET  /api/history
clearHistory()                  // DELETE /api/history
addFavorite(product)            // POST /api/favorites
getFavorites()                  // GET  /api/favorites
removeFavorite(productId)       // DELETE /api/favorites/{id}
```

`VITE_API_URL` is read at build time. In development, Vite proxies
`/api/*` to `http://localhost:8000` automatically.

---

## 13. Data Storage

| File | Purpose | Format |
|------|---------|--------|
| `backend/products.json` | Local product catalogue (10 products) | JSON array |
| `backend/data/search_history.json` | Persistent search history (100-entry cap) | JSON array |
| `backend/data/favorites.json` | Saved favourite products | JSON array |

Both `search_history.json` and `favorites.json` use `threading.Lock` for
thread-safe reads and writes.

---

## 14. Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key — get free at https://console.groq.com/keys |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `SERP_API_KEY` | No | — | SerpAPI key for real Amazon results — get at https://serpapi.com |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | Comma-separated CORS origins |
| `APP_TITLE` | No | `AI Shopping Assistant API` | Swagger title |
| `APP_VERSION` | No | `4.0.0` | Version string |
| `DEBUG` | No | `false` | Enable debug logging |
| `HOST` | No | `0.0.0.0` | Server bind host |
| `PORT` | No | `8000` | Server bind port |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | `""` (proxied) | Production backend URL |

---

## 15. Setup & Running Locally

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- A Groq API key (free): https://console.groq.com/keys

### Backend Setup

```cmd
cd shopping-assistant-agent\backend

REM Create virtual environment
python -m venv .venv

REM Activate (Windows)
.venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Create .env from template
copy .env.example .env
```

Edit `.env` and set your `GROQ_API_KEY`. Then:

```cmd
uvicorn app:app --reload --port 8000
```

Expected startup output:
```
[GroqService] Using model: llama-3.3-70b-versatile
[AmazonService] No SERP_API_KEY — using Local Products Fallback
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Frontend Setup

```cmd
cd shopping-assistant-agent\frontend
npm install
npm run dev
```

Open: **http://localhost:5173**

Swagger docs: **http://localhost:8000/docs**

### Enable Real Amazon Search (Optional)

1. Get a free key at https://serpapi.com
2. Add to `backend/.env`: `SERP_API_KEY=your_key_here`
3. Restart the backend

Startup will show:
```
[AmazonService] SERP_API_KEY found — will attempt SerpAPI first
```
