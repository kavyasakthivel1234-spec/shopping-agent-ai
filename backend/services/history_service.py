"""
history_service.py
------------------
Manages persistent search history stored as a flat JSON file.

Enhanced in this version:
  - save() now accepts and stores: query, timestamp, top_pick,
    alternatives (names only), confidence, and assistant_response
  - Thread-safe read/write with threading.Lock
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from config import settings

MAX_HISTORY_ENTRIES = 100


class HistoryService:
    """Provides CRUD operations on the search history file."""

    def __init__(self, path: Path = None):
        self._path = path or settings.SEARCH_HISTORY_PATH
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write([])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        query:               str,
        top_pick:            dict | None,
        confidence:          float,
        alternatives:        list[dict] | None = None,
        assistant_response:  str | None        = None,
    ) -> dict:
        """
        Append a new search entry to the history file.

        Args:
            query:               The raw user query string.
            top_pick:            Top recommended product dict (or None).
            confidence:          Orchestrator confidence score (0.0–1.0).
            alternatives:        List of alternative product dicts (or None).
            assistant_response:  Plain-text summary shown to the user (or None).

        Returns:
            The saved entry dict.
        """
        # Store only lightweight summaries to keep the file small
        alt_summary = []
        if alternatives:
            for p in alternatives[:5]:   # store at most 5
                alt_summary.append({
                    "id":    p.get("id"),
                    "name":  p.get("name"),
                    "price": p.get("price"),
                })

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query":     query,
            "top_pick":  {
                "id":    top_pick.get("id"),
                "name":  top_pick.get("name"),
                "price": top_pick.get("price"),
            } if top_pick else None,
            "alternatives":       alt_summary,
            "confidence":         round(confidence, 2),
            "assistant_response": assistant_response,
        }

        with self._lock:
            history = self._read()
            history.insert(0, entry)
            history = history[:MAX_HISTORY_ENTRIES]
            self._write(history)

        return entry

    def get_all(self) -> list[dict]:
        """Return the full history list (newest first)."""
        with self._lock:
            return self._read()

    def clear(self) -> None:
        """Delete all search history entries."""
        with self._lock:
            self._write([])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read(self) -> list:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write(self, data: list) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
