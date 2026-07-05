"""
comparison_agent.py
-------------------
Agent responsible for generating AI-powered product comparisons.

Role in the multi-agent workflow:
    (Optional) called by Orchestrator when two product IDs are supplied

    ComparisonAgent             ← THIS AGENT
          ↓
    { product1, product2, comparison, winner, summary }

This agent wraps ComparisonService and enforces:
  - ID validation (cannot compare a product with itself)
  - Consistent agent result envelope

Agents call services — they do NOT contain business logic themselves.
"""

import logging
from services.comparison import ComparisonService

logger = logging.getLogger(__name__)


class ComparisonAgent:
    """
    Orchestrates a side-by-side AI comparison of two products.

    Accepts:
        product1_id, product2_id  — product IDs from products.json

    Returns:
        {
            "agent": "ComparisonAgent",
            "status": "success",
            "data": {
                "product1":   { …product fields },
                "product2":   { …product fields },
                "comparison": {
                    "camera":  { "product1": "…", "product2": "…" },
                    "battery": { "product1": "…", "product2": "…" },
                    "price":   { "product1": "…", "product2": "…" },
                    "winner":  "Samsung Galaxy M35",
                    "summary": "…"
                }
            }
        }
    """

    NAME = "ComparisonAgent"

    def __init__(self, comparison_service: ComparisonService):
        """
        Args:
            comparison_service: Shared ComparisonService instance.
        """
        self.comparison_service = comparison_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, product1_id: str, product2_id: str) -> dict:
        """
        Execute the product comparison task.

        Args:
            product1_id: ID of the first product  (e.g. "sp-001").
            product2_id: ID of the second product (e.g. "sp-002").

        Returns:
            Agent result envelope with full comparison data.
        """
        logger.info(
            "[%s] Comparing %r vs %r", self.NAME, product1_id, product2_id
        )

        # Guard: comparing a product against itself is meaningless
        if product1_id == product2_id:
            return self._error("Cannot compare a product with itself.")

        try:
            result = self.comparison_service.compare_products(
                product1_id, product2_id
            )
        except KeyError as exc:
            logger.warning("[%s] Product not found: %s", self.NAME, exc)
            return self._error(f"Product not found: {exc}")
        except (RuntimeError, ValueError) as exc:
            logger.error("[%s] Comparison service error: %s", self.NAME, exc)
            return self._error(f"Comparison failed: {exc}")

        logger.info(
            "[%s] Winner: %s",
            self.NAME,
            result.get("comparison", {}).get("winner", "unknown"),
        )

        return self._success(result)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _success(self, data: dict) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
