<<<<<<< HEAD
# AI Shopping Assistant Agent

An AI-powered shopping assistant built with **React + Vite** (frontend) and **Python FastAPI** (backend). It uses **Groq + Llama 3** to deliver personalised product recommendations, comparisons, and review summaries through a multi-agent automation pipeline.

---

## Project Structure

```
shopping-assistant-agent/
│
├── frontend/                        # React + Vite application
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   ├── pages/                   # Page-level components
│   │   ├── services/api.js          # Centralised API call helpers
│   │   ├── App.jsx                  # Root component + tab navigation
│   │   └── main.jsx                 # Entry point
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json                  # Vercel deployment config
│
├── backend/                         # FastAPI application
│   ├── app.py                       # Entry point + CORS + router mounting
│   ├── config.py                    # Environment-based settings
│   ├── requirements.txt             # Python dependencies
│   ├── products.json                # Product catalogue
│   ├── data/
│   │   ├── search_history.json      # Persistent search history
│   │   └── favorites.json           # Persistent favourites
│   ├── agents/
│   │   ├── orchestrator.py          # ShoppingAssistantOrchestrator
│   │   ├── requirement_agent.py     # Extracts requirements from query
│   │   ├── recommendation_agent.py  # Filters + scores products
│   │   ├── review_agent.py          # Summarises product reviews
│   │   └── comparison_agent.py      # Side-by-side product comparison
│   ├── services/
│   │   ├── gemini_service.py        # AI service (Groq + Llama 3)
│   │   ├── recommendation.py        # Recommendation engine
│   │   ├── comparison.py            # Comparison logic
│   │   ├── pros_cons_service.py     # Pros & cons generation
│   │   ├── review_summary.py        # Review summarisation
│   │   ├── history_service.py       # Search history (JSON file)
│   │   └── favorite_service.py      # Favourites (JSON file)
│   ├── routes/
│   │   ├── recommendation_routes.py # Phase 1 + 2 endpoints
│   │   ├── assistant_routes.py      # Phase 3 multi-agent endpoint
│   │   ├── history_routes.py        # Phase 4 history endpoints
│   │   └── favorite_routes.py       # Phase 4 favourites endpoints
│   └── models/
│       └── product_model.py         # Pydantic request/response models
│
├── docs/
│   ├── ai_automation_flow.md        # Multi-agent architecture diagram
│   └── project_flow.md              # Request flow documentation
│
├── render.yaml                      # Render.com deployment config
├── README.md
└── .gitignore
```

---

## AI Architecture — Multi-Agent Pipeline

```
User Query
    ↓
RequirementAgent     → Groq (Llama 3): extract category, budget, features
    ↓
RecommendationAgent  → Filter + score products from catalogue
    ↓
ReviewAgent          → Groq (Llama 3): summarise mock reviews
    ↓
Final Response       → requirements + top_pick + alternatives + review_summary + confidence
```

---

## Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.11
- A **free Groq API key** — get one in 30 seconds at https://console.groq.com/keys

---

## Setup & Running

### 1. Backend

```bash
cd shopping-assistant-agent/backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies (includes groq SDK)
pip install -r requirements.txt

# Create your .env file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Open .env and set your Groq API key:
#   GROQ_API_KEY=your_key_here

# Start the development server
uvicorn app:app --reload --port 8000
```

On startup you should see:
```
[GroqService] Using model: llama-3.3-70b-versatile
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Backend API: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd shopping-assistant-agent/frontend

npm install
npm run dev
```

Frontend UI: `http://localhost:5173`

---

## API Endpoints

| Phase | Method | Path | Description |
|-------|--------|------|-------------|
| — | GET | `/health` | Liveness probe |
| 1 | POST | `/api/recommend` | AI requirement extraction + scored products |
| 2 | GET | `/api/pros-cons/{id}` | AI-generated pros & cons |
| 2 | POST | `/api/compare` | AI side-by-side product comparison |
| 2 | GET | `/api/reviews/{id}/summary` | AI review summarisation |
| 3 | POST | `/api/assistant` | Full multi-agent pipeline |
| 4 | GET | `/api/history` | Search history |
| 4 | DELETE | `/api/history` | Clear search history |
| 4 | POST | `/api/favorites` | Add to favourites |
| 4 | GET | `/api/favorites` | List favourites |
| 4 | DELETE | `/api/favorites/{id}` | Remove from favourites |

### Example — POST /api/assistant

**Request**
```json
{ "query": "I need a smartphone under ₹20000 with a good camera and long battery life" }
```

**Response**
```json
{
  "requirements":   { "category": "smartphone", "budget": 20000, "features": ["good camera", "long battery life"] },
  "top_pick":       { "id": "sp-001", "name": "Samsung Galaxy M35", "price": 18000, "score": 20 },
  "alternatives":   [ { "id": "sp-002", "name": "Realme Narzo 80", "price": 17000, "score": 20 } ],
  "review_summary": { "liked": ["Battery", "Camera"], "disliked": ["Charging Speed"], "review_count": 5 },
  "confidence":     0.92,
  "pipeline":       ["RequirementAgent", "RecommendationAgent", "ReviewAgent"]
}
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key from https://console.groq.com/keys |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | Comma-separated CORS origins |
| `APP_VERSION` | No | `4.0.0` | API version string |
| `DEBUG` | No | `false` | Enable debug logging |
| `HOST` | No | `0.0.0.0` | Server bind host |
| `PORT` | No | `8000` | Server bind port |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Llama 3.3 70B via Groq API |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Frontend | React 18 · Vite 5 |
| Data | `products.json` + JSON file storage |
| Multi-agent | Custom agent classes (no CrewAI / LangChain) |
| Deployment | Render (backend) · Vercel (frontend) |

---

## Features

- 🔍 **Smart Recommendations** — AI extracts requirements from natural language and scores matching products
- ⚖️ **Product Comparison** — Side-by-side AI comparison with a declared winner
- ✅❌ **Pros & Cons** — AI-generated pros and cons for any product
- 💬 **Review Summary** — Liked / disliked topic extraction from reviews
- 🤖 **Multi-Agent Chat** — Conversational interface with pipeline transparency
- ❤️ **Favourites** — Save products for later
- 🕓 **History** — Browse and clear past searches
- 🌙 **Dark Mode** — Theme toggle with localStorage persistence
- 📱 **Mobile Responsive** — Layouts optimised from 320 px to 1440 px
=======
# shopping-agent-ai
>>>>>>> 5c662818038626450030fa62d81d4a9499e0de1e
"# agent" 
