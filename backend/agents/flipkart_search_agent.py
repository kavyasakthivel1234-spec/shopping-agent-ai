"""
flipkart_search_agent.py
------------------------
Agent responsible for searching Flipkart for products that match
the extracted user requirements.

Architecture position:
    RequirementAgent (structured requirements)
          ↓
    FlipkartSearchAgent         ← THIS AGENT
          ↓
    list of Flipkart product dicts (each tagged source="Flipkart")

Single responsibility:
  - Accept requirements from the orchestrator
  - Call FlipkartService.search_products()
  - Return a normalised agent result envelope

This agent contains NO business logic — that lives in FlipkartService.
To switch from simulated data to the real Flipkart API, only FlipkartService
needs to change.
"""

import logging
from services.flipkart_service import FlipkartService

logger = logging.getLogger(__name__)


class FlipkartSearchAgent:
    """
    Searches Flipkart (via FlipkartService) for products matching requirements.

    Input:
        requirements: { "category": str, "budget": float, "features": list }

    Output (success):
        {
            "agent":  "FlipkartSearchAgent",
            "status": "success",
            "data":   [
                {
                    "id":       "fk-sp-001",
                    "name":     "Vivo V29e 5G",
                    "price":    22999,
                    "category": "smartphone",
                    "camera":   "50MP good camera",
                    "battery":  "4800mAh",
                    "brand":    "Vivo",
                    "rating":   4.3,
                    "source":   "Flipkart"
                },
                ...
            ]
        }

    Output (error):
        { "agent": "FlipkartSearchAgent", "status": "error", "error": "..." }
    """

    NAME = "FlipkartSearchAgent"

    def __init__(self, flipkart_service: FlipkartService = None):
        """
        Args:
            flipkart_service: FlipkartService instance (injected or created here).
        """
        self.flipkart_service = flipkart_service or FlipkartService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, requirements: dict) -> dict:
        """
        Execute the Flipkart product search.

        Args:
            requirements: Validated dict from RequirementAgent.

        Returns:
            Agent result envelope with a list of matching products.
        """
        logger.info(
            "[%s] Searching | category=%r budget=%s",
            self.NAME,
            requirements.get("category"),
            requirements.get("budget"),
        )

        try:
            products = self.flipkart_service.search_products(requirements)
        except Exception as exc:
            logger.error("[%s] FlipkartService error: %s", self.NAME, exc)
            return self._error(f"Flipkart search failed: {exc}")

        logger.info("[%s] Found %d products", self.NAME, len(products))
        return self._success(products)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _success(self, data: list) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
