"""
recommendation_agent.py
------------------------
Agent responsible for scoring and ranking a product pool.

Updated for multi-source: now accepts an optional product_pool kwarg
so the orchestrator can pass the merged Amazon + Flipkart results.
Falls back to local products.json when no pool is supplied.
"""

import logging
from services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

MAX_SCORE = 30   # camera(10) + battery(10) + 5g(5) + fast_charging(5)


class RecommendationAgent:
    """
    Filters, scores, and ranks products from the provided pool.

    Accepts:
        requirements:  dict from RequirementAgent
        product_pool:  optional list of products (Amazon + Flipkart merged)

    Returns agent result envelope with top_pick, alternatives, confidence.
    """

    NAME = "RecommendationAgent"

    def __init__(self, recommendation_service: RecommendationService):
        self.recommendation_service = recommendation_service

    def run(self, requirements: dict, product_pool: list[dict] | None = None) -> dict:
        """
        Execute the recommendation task.

        Args:
            requirements:  { "category", "budget", "features" }
            product_pool:  merged multi-source product list (optional)
        """
        logger.info("[%s] Running | pool_size=%d", self.NAME,
                    len(product_pool) if product_pool is not None else -1)

        try:
            result = self.recommendation_service.recommend_products(
                requirements,
                product_pool=product_pool,
            )
        except Exception as exc:
            logger.error("[%s] Service error: %s", self.NAME, exc)
            return self._error(f"Recommendation service failed: {exc}")

        top_pick     = result.get("top_pick")
        alternatives = result.get("alternatives", [])
        confidence   = self._calculate_confidence(top_pick, alternatives)

        logger.info(
            "[%s] top=%s source=%s | alternatives=%d | confidence=%.2f",
            self.NAME,
            top_pick["name"]          if top_pick else "None",
            top_pick.get("source","-") if top_pick else "-",
            len(alternatives),
            confidence,
        )

        return self._success({
            "top_pick":     top_pick,
            "alternatives": alternatives,
            "confidence":   confidence,
        })

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_confidence(self, top_pick: dict | None, alternatives: list) -> float:
        if top_pick is None:
            return 0.0
        top_score   = top_pick.get("score", 0)
        base        = top_score / MAX_SCORE if MAX_SCORE > 0 else 0.0
        depth_bonus = min(len(alternatives) * 0.04, 0.20)
        if top_score == 0 and top_pick:
            base = 0.50
        return round(min(base + depth_bonus, 1.0), 2)

    def _success(self, data: dict) -> dict:
        return {"agent": self.NAME, "status": "success", "data": data}

    def _error(self, message: str) -> dict:
        return {"agent": self.NAME, "status": "error", "error": message}
