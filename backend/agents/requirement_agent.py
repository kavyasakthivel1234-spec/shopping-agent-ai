"""
requirement_agent.py
--------------------
Agent responsible for understanding what the user wants.

Role in the multi-agent workflow:
    User query (raw text)
          ↓
    RequirementAgent          ← THIS AGENT
          ↓
    Structured requirements dict

This agent is the entry point of every orchestrated workflow. It wraps
GroqService.extract_requirements and adds:
  - Input validation
  - Logging / tracing metadata
  - A normalised, typed output that downstream agents can rely on

Agents call services — they do NOT contain business logic themselves.
"""

import logging
from services.groq_service import GroqService

logger = logging.getLogger(__name__)


class RequirementAgent:
    """
    Extracts structured shopping requirements from a raw user query.

    Accepts:
        "I need a smartphone under ₹20000 with a good camera"

    Returns:
        {
            "agent": "RequirementAgent",
            "status": "success",
            "data": {
                "category": "smartphone",
                "budget": 20000.0,
                "features": ["good camera"]
            }
        }
    """

    # Agent identity — used in orchestrator logs and response metadata
    NAME = "RequirementAgent"

    def __init__(self, groq_service: GroqService):
        """
        Args:
            groq_service: Shared GroqService instance (injected by orchestrator).
        """
        self.groq_service = groq_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, query: str) -> dict:
        """
        Execute the requirement extraction task.

        Args:
            query: Raw natural-language user input.

        Returns:
            Agent result envelope:
            {
                "agent":  "RequirementAgent",
                "status": "success" | "error",
                "data":   { category, budget, features }  # on success
                "error":  "…"                              # on failure
            }
        """
        logger.info("[%s] Processing query: %r", self.NAME, query)

        if not query or not query.strip():
            return self._error("Query must not be empty.")

        try:
            requirements = self.groq_service.extract_requirements(query.strip())
        except RuntimeError as exc:
            # Groq API unavailable
            logger.error("[%s] Groq API error: %s", self.NAME, exc)
            return self._error(f"AI service unavailable: {exc}")
        except ValueError as exc:
            # Groq returned unparseable JSON
            logger.error("[%s] JSON parse error: %s", self.NAME, exc)
            return self._error(f"AI response parse error: {exc}")

        logger.info("[%s] Extracted: %s", self.NAME, requirements)
        return self._success(requirements)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _success(self, data: dict) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
