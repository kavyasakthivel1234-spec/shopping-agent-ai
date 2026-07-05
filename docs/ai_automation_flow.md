# AI Automation Flow — Phase 3 Multi-Agent Architecture

## Overview

Phase 3 converts the single-service backend into a **multi-agent AI automation
system**.  Each agent is a focused, single-responsibility unit that accepts a
well-defined input, calls one or more services, and returns a normalised result
envelope.

All agents are coordinated by the **ShoppingAssistantOrchestrator**, which
wires them together and manages the pipeline flow.

---

## Full Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface                             │
│                                                                     │
│   Recommendations Tab          │       AI Assistant Tab            │
│   (Phase 1 + 2 search UI)      │   (Phase 3 chat interface)        │
└──────────────┬─────────────────┴──────────────┬────────────────────┘
               │                                 │
        POST /api/recommend              POST /api/assistant
        POST /api/compare                         │
        GET  /api/pros-cons/{id}                  ▼
        GET  /api/reviews/{id}/summary ┌─────────────────────────┐
               │                       │ ShoppingAssistantOrch.  │
               │                       │   process_query(query)  │
               │                       └──────────┬──────────────┘
               │                                  │
               ▼                                  ▼
        ┌─────────────────────────────────────────────────────────┐
        │                   Multi-Agent Pipeline                  │
        │                                                         │
        │   Step 1: RequirementAgent                              │
        │   ┌──────────────────────────────────────────────────┐  │
        │   │  Input : "smartphone under ₹20000 good camera"   │  │
        │   │  Calls : GeminiService.extract_requirements()    │  │
        │   │  Output: { category, budget, features }          │  │
        │   └──────────────────────┬───────────────────────────┘  │
        │                          │ requirements dict             │
        │   Step 2: RecommendationAgent                            │
        │   ┌──────────────────────▼───────────────────────────┐  │
        │   │  Input : { category, budget, features }          │  │
        │   │  Calls : RecommendationService.recommend()       │  │
        │   │  Output: { top_pick, alternatives, confidence }  │  │
        │   └──────────────────────┬───────────────────────────┘  │
        │                          │ top_pick.id                   │
        │   Step 3: ReviewAgent                                    │
        │   ┌──────────────────────▼───────────────────────────┐  │
        │   │  Input : product_id (from top_pick)              │  │
        │   │  Calls : ReviewSummaryService.summarise()        │  │
        │   │  Output: { liked[], disliked[], review_count }   │  │
        │   └──────────────────────┬───────────────────────────┘  │
        │                          │                               │
        │   Step 4: ComparisonAgent (optional — separate route)    │
        │   ┌──────────────────────▼───────────────────────────┐  │
        │   │  Input : product1_id, product2_id                │  │
        │   │  Calls : ComparisonService.compare_products()    │  │
        │   │  Output: { camera, battery, price, winner }      │  │
        │   └──────────────────────┬───────────────────────────┘  │
        │                          │                               │
        └──────────────────────────┼─────────────────────────────-┘
                                   │
                                   ▼
                      ┌────────────────────────┐
                      │   Final Response        │
                      │  {                      │
                      │    requirements,        │
                      │    top_pick,            │
                      │    alternatives,        │
                      │    review_summary,      │
                      │    confidence,          │
                      │    pipeline: [          │
                      │      "RequirementAgent",│
                      │      "RecommendationAge"│
                      │      "ReviewAgent"      │
                      │    ]                    │
                      │  }                      │
                      └────────────────────────┘
```

---

## Agent Responsibilities

### 1. RequirementAgent

| Item     | Detail |
|----------|--------|
| Input    | Raw user query string |
| Output   | `{ category, budget, features }` |
| Calls    | `GeminiService.extract_requirements()` |
| Fails on | Empty query, Gemini API error, JSON parse error |

### 2. RecommendationAgent

| Item     | Detail |
|----------|--------|
| Input    | Requirements dict from RequirementAgent |
| Output   | `{ top_pick, alternatives, confidence }` |
| Calls    | `RecommendationService.recommend_products()` |
| Fails on | Service errors |
| Note     | Confidence is a heuristic score (0.0–1.0) based on match quality |

### 3. ReviewAgent

| Item     | Detail |
|----------|--------|
| Input    | `product_id` from top_pick |
| Output   | `{ product_id, review_count, liked[], disliked[] }` |
| Calls    | `ReviewSummaryService.summarise()` |
| Fails on | Gemini API error (non-fatal — orchestrator continues without reviews) |

### 4. ComparisonAgent *(optional)*

| Item     | Detail |
|----------|--------|
| Input    | `product1_id`, `product2_id` |
| Output   | `{ product1, product2, comparison: { camera, battery, price, winner, summary } }` |
| Calls    | `ComparisonService.compare_products()` |
| Fails on | Invalid product IDs, same IDs, Gemini API error |

---

## Orchestrator: ShoppingAssistantOrchestrator

```python
orchestrator = ShoppingAssistantOrchestrator()

# Main pipeline (RequirementAgent → RecommendationAgent → ReviewAgent)
result = orchestrator.process_query("smartphone under 20000 good camera")

# Optional comparison sub-pipeline (ComparisonAgent only)
comparison = orchestrator.compare("sp-001", "sp-002")
```

### Error handling

- If **RequirementAgent** or **RecommendationAgent** fails → pipeline halts,
  returns `{ error, failed_agent, pipeline }`.
- If **ReviewAgent** fails → non-fatal, `review_summary` is `null` in the
  response, pipeline continues.

---

## Service Architecture

```
GeminiService               ← AI communication (all Gemini calls)
      ↓  (used by)
RequirementAgent            uses → GeminiService.extract_requirements
ReviewAgent                 uses → ReviewSummaryService → GeminiService.summarise_reviews
ComparisonAgent             uses → ComparisonService → GeminiService.generate_comparison
RecommendationAgent         uses → RecommendationService (no Gemini calls)
      ↓  (coordinated by)
ShoppingAssistantOrchestrator
      ↓  (called by)
assistant_routes.py  → POST /api/assistant
```

---

## API Endpoints Summary

| Phase | Method | Path | Description |
|-------|--------|------|-------------|
| 1 | GET | `/health` | Liveness probe |
| 1 | POST | `/api/recommend` | Single-agent recommendation |
| 2 | GET | `/api/pros-cons/{id}` | AI pros & cons |
| 2 | POST | `/api/compare` | AI product comparison |
| 2 | GET | `/api/reviews/{id}/summary` | Review summarisation |
| **3** | **POST** | **`/api/assistant`** | **Multi-agent pipeline** |

---

## Confidence Score Calculation

The confidence score (0.0–1.0) is computed by RecommendationAgent:

```
base        = top_pick.score / MAX_SCORE        (MAX_SCORE = 20)
depth_bonus = min(len(alternatives) × 0.05, 0.20)
confidence  = clamp(base + depth_bonus, 0.0, 1.0)
```

If a product matched the category/budget filters but scored 0 on features,
the base confidence defaults to 0.50 (indicating a partial match).

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Google Gemini 1.5 Flash |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Frontend | React 18 · Vite 5 |
| Data | Static `products.json` + mock reviews |
| Multi-agent | Custom agent classes (no CrewAI / LangChain) |
