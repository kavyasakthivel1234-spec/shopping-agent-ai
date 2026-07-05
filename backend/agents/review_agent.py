"""
review_agent.py
---------------
Agent responsible for fetching and summarising product reviews.

Role in the multi-agent workflow:
    RecommendationAgent (top_pick product)
          ↓
    ReviewAgent                 ← THIS AGENT
          ↓
    { product_id, liked[], disliked[], review_count }

This agent wraps ReviewSummaryService so the orchestrator does not need to
know about mock data or AI summarisation internals.

Agents call services — they do NOT contain business logic themselves.
"""

import logging
from services.review_summary import ReviewSummaryService

logger = logging.getLogger(__name__)


class ReviewAgent:
    """
    Fetches mock reviews and produces an AI-generated liked/disliked summary
    for a given product.

    Accepts:
        product_id  — e.g. "sp-001"

    Returns:
        {
            "agent": "ReviewAgent",
            "status": "success",
            "data": {
                "product_id":   "sp-001",
                "review_count": 5,
                "liked":    ["Battery", "Camera"],
                "disliked": ["Charging Speed"]
            }
        }
    """

    NAME = "ReviewAgent"

    def __init__(self, review_summary_service: ReviewSummaryService):
        """
        Args:
            review_summary_service: Shared ReviewSummaryService instance.
        """
        self.review_summary_service = review_summary_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, product_id: str) -> dict:
        """
        Fetch and summarise reviews for the given product.

        Args:
            product_id: The product's "id" field from products.json.

        Returns:
            Agent result envelope with liked/disliked topic lists.
        """
        logger.info("[%s] Summarising reviews for product: %r", self.NAME, product_id)

        if not product_id:
            return self._error("product_id must not be empty.")

        try:
            summary = self.review_summary_service.summarise(product_id)
        except (RuntimeError, ValueError) as exc:
            logger.error("[%s] ReviewSummaryService error: %s", self.NAME, exc)
            return self._error(f"Review summarisation failed: {exc}")

        logger.info(
            "[%s] liked=%s | disliked=%s",
            self.NAME,
            summary.get("liked"),
            summary.get("disliked"),
        )

        return self._success(summary)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _success(self, data: dict) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
