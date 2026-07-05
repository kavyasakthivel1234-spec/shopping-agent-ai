"""
recommendation.py
-----------------
Recommendation engine — scoring and ranking only.

For REAL products (source_type="Real", data_mode="amazon"):
  - NO category filtering — SerpAPI already fetched the right products
  - NO budget filtering — AmazonService already filtered by price
  - Only scored by rating, review count, and feature matches

For LOCAL products (legacy fallback — should not be reached in production):
  - Original category + budget filtering applies
"""

import logging

logger = logging.getLogger(__name__)

CATEGORY_ALIASES: dict[str, str] = {
    "phone":      "smartphone",
    "mobile":     "smartphone",
    "smartphone": "smartphone",
    "android":    "smartphone",
    "iphone":     "smartphone",
    "watch":      "smartwatch",
    "smartwatch": "smartwatch",
    "earbuds":    "headphones",
    "earphone":   "headphones",
    "headphone":  "headphones",
    "laptop":     "laptop",
    "notebook":   "laptop",
    "tab":        "tablet",
    "tablet":     "tablet",
}


class RecommendationService:
    """
    Scores and ranks a product pool.
    Real products are never filtered — just scored and sorted.
    """

    def __init__(self):
        pass  # no local catalogue needed

    def recommend_products(
        self,
        requirements: dict,
        product_pool: list[dict] | None = None,
    ) -> dict:
        if not product_pool:
            logger.warning("[RecommendationService] Empty product pool — returning no results")
            return {"top_pick": None, "alternatives": []}

        features = [f.lower().strip() for f in requirements.get("features", [])]

        # Separate real vs local
        real_products  = [p for p in product_pool if p.get("source_type") == "Real"]
        local_products = [p for p in product_pool if p.get("source_type") != "Real"]

        if real_products:
            # Score real products — no filtering
            scored = sorted(
                [{**p, "score": self._score(p, features)} for p in real_products],
                key=lambda x: x["score"],
                reverse=True,
            )
            logger.info(
                "[RecommendationService] %d real products scored. Top: %s",
                len(scored),
                scored[0]["name"] if scored else "None",
            )
        else:
            # Legacy local path
            budget   = float(requirements.get("budget", 0))
            category = CATEGORY_ALIASES.get(
                requirements.get("category", "").lower(), requirements.get("category", "")
            )
            filtered = self._filter_local(local_products, category, budget)
            scored   = sorted(
                [{**p, "score": self._score(p, features)} for p in filtered],
                key=lambda x: x["score"],
                reverse=True,
            )
            logger.info("[RecommendationService] %d local products after filter", len(scored))

        return {
            "top_pick":     scored[0] if scored else None,
            "alternatives": scored[1:] if len(scored) > 1 else [],
        }

    def _filter_local(
        self,
        pool:     list[dict],
        category: str,
        budget:   float,
    ) -> list[dict]:
        results = []
        for p in pool:
            if category:
                pc = CATEGORY_ALIASES.get(p.get("category", "").lower(), p.get("category", ""))
                cat = CATEGORY_ALIASES.get(category, category)
                if cat not in pc and pc not in cat:
                    continue
            price = p.get("price")
            if budget > 0 and price is not None and price > budget:
                continue
            results.append(p)
        return results

    def _score(self, product: dict, features: list[str]) -> int:
        score = 0

        # Rating — highest weight
        rating = product.get("rating")
        if rating:
            try:
                r = float(rating)
                if r >= 4.5:
                    score += 30
                elif r >= 4.0:
                    score += 20
                elif r >= 3.5:
                    score += 10
            except (TypeError, ValueError):
                pass

        # Review count — popularity signal
        reviews = product.get("reviews")
        if reviews:
            try:
                rc = int(reviews)
                if rc > 10000:
                    score += 10
                elif rc > 1000:
                    score += 6
                elif rc > 100:
                    score += 3
            except (TypeError, ValueError):
                pass

        # Feature keyword matching in name/specs
        name_text = (
            (product.get("name") or "")
            + " " + (product.get("camera") or "")
            + " " + (product.get("battery") or "")
        ).lower()

        for feat in features:
            if feat in name_text:
                score += 5

        return score
