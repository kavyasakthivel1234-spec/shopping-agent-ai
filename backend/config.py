"""
config.py
---------
Centralised, environment-based configuration for the FastAPI backend.

FIX BUG-02: All settings are now evaluated inside __init__ so they are
resolved AFTER load_dotenv() has run, not at class-body evaluation time.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file. On Render/Railway env vars are injected directly — no-op.
load_dotenv()

BASE_DIR = Path(__file__).parent


class Settings:
    """
    Centralised settings object.
    All attributes are set in __init__ so os.getenv() runs AFTER
    load_dotenv() has already populated the environment.
    """

    def __init__(self):
        # ── Application ─────────────────────────────────────────────
        self.APP_TITLE:   str  = os.getenv("APP_TITLE",   "AI Shopping Assistant API")
        self.APP_VERSION: str  = os.getenv("APP_VERSION", "4.0.0")
        self.DEBUG:       bool = os.getenv("DEBUG", "false").lower() == "true"

        # ── Groq AI ──────────────────────────────────────────────────
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

        # ── CORS ─────────────────────────────────────────────────────
        raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        self.ALLOWED_ORIGINS: list[str] = [
            o.strip() for o in raw_origins.split(",") if o.strip()
        ]

        # ── Data paths ───────────────────────────────────────────────
        self.PRODUCTS_PATH:       Path = BASE_DIR / "products.json"
        self.SEARCH_HISTORY_PATH: Path = BASE_DIR / "data" / "search_history.json"

        # ── Server ───────────────────────────────────────────────────
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))


# Singleton — import this everywhere
settings = Settings()
