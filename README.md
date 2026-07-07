# Shopping Agent AI

An AI-powered shopping assistant built with **React + Vite** (frontend) and **Python FastAPI** (backend).

Uses **Groq + Llama 3.3** for natural language understanding and **SerpAPI** for real Amazon product search.

No authentication required — opens directly to the AI Shopping Assistant.

---

## Live Demo

- Frontend: https://shopping-assistant-frontend-bma0.onrender.com
- Backend API: https://shopping-assistant-api-vhwh.onrender.com
- Swagger docs: https://shopping-assistant-api-vhwh.onrender.com/docs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python FastAPI + Uvicorn |
| AI Model | Groq — Llama 3.3 70B |
| Product Search | SerpAPI (real Amazon India) |
| Database | MongoDB Atlas (Motor async driver) |
| Deployment | Render.com |

---

## Features

- AI Shopping Assistant — natural language product search
- Real Amazon products via SerpAPI
- Product comparison, pros/cons, review summaries
- Multi-agent pipeline (Intent → Requirements → Search → Recommend → Review)
- Search history (MongoDB)
- Chat persistence (sessionStorage + MongoDB)

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # fill in GROQ_API_KEY, MONGODB_URI, SERP_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables (backend)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key from https://console.groq.com/keys |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `SERP_API_KEY` | Optional | SerpAPI key for real Amazon search |
| `ALLOWED_ORIGINS` | Yes (prod) | Comma-separated frontend URLs |
| `MODEL_NAME` | No | Default: `llama-3.3-70b-versatile` |
