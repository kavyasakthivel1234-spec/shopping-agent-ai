"""
amazon_search_agent.py
----------------------
Agent responsible for searching Amazon for products that match
the extracted user requirements.

Architecture position:
    RequirementAgent (structured requirements)
          ↓
    AmazonSearchAgent           ← THIS AGENT
          ↓
    list of Amazon product dicts (each tagged source="Amazon")

Single responsibility:
  - Accept requirements from the orchestrator
  - Call AmazonService.search_products()
  - Return a normalised agent result envelope

This agent contains NO business logic — that lives in AmazonService.
To switch from simulated data to the real Amazon API, only AmazonService
needs to change.
"""

import logging
from services.amazon_service import AmazonService

logger = logging.getLogger(__name__)


class AmazonSearchAgent:
    """
    Searches Amazon (via AmazonService) for products matching requirements.

    Input:
        requirements: { "category": str, "budget": float, "features": list }

    Output (success):
        {
            "agent":  "AmazonSearchAgent",
            "status": "success",
            "data":   [
                {
                    "id":       "amz-sp-001",
                    "name":     "Samsung Galaxy S23 FE",
                    "price":    34999,
                    "category": "smartphone",
                    "camera":   "50MP triple camera",
                    "battery":  "4500mAh",
                    "brand":    "Samsung",
                    "rating":   4.4,
                    "source":   "Amazon"
                },
                ...
            ]
        }

    Output (error):
        { "agent": "AmazonSearchAgent", "status": "error", "error": "..." }
    """

    NAME = "AmazonSearchAgent"

    def __init__(self, amazon_service: AmazonService = None):
        """
        Args:
            amazon_service: AmazonService instance (injected or created here).
        """
        self.amazon_service = amazon_service or AmazonService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, requirements: dict) -> dict:
        """
        Execute the Amazon product search.

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
            products = self.amazon_service.search_products(requirements)
        except Exception as exc:
            logger.error("[%s] AmazonService error: %s", self.NAME, exc)
            return self._error(f"Amazon search failed: {exc}")

        logger.info("[%s] Found %d products", self.NAME, len(products))
        return self._success(products)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _success(self, data: list) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
