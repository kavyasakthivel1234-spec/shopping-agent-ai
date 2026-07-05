"""
local_product_service.py
------------------------
Reads products.json and returns filtered results tagged as
source="Amazon", source_type="Local".

This service is used as the fallback inside AmazonService when:
  - SERP_API_KEY is not set, OR
  - The SerpAPI call fails / returns no results

Architecture position:
    AmazonService → LocalProductService (fallback only)

Keeping this as a separate class means the fallback logic is isolated
and testable independently of AmazonService.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PRODUCTS_PATH = Path(__file__).parent.parent / "products.json"

_CATEGORY_ALIASES: dict[str, str] = {
    "phone":      "smartphone",
    "mobile":     "smartphone",
    "smartphone": "smartphone",
    "android":    "smartphone",
    "iphone":     "smartphone",
    "watch":      "smartwatch",
    "smartwatch": "smartwatch",
    "wearable":   "smartwatch",
    "earbuds":    "headphones",
    "earphone":   "headphones",
    "headphone":  "headphones",
    "headset":    "headphones",
    "earbud":     "headphones",
    "laptop":     "laptop",
    "notebook":   "laptop",
    "tab":        "tablet",
    "tablet":     "tablet",
    "ipad":       "tablet",
}


class LocalProductService:
    """
    Reads products.json and returns matching results.

    Every product is tagged with:
        source      = "Amazon"   (conceptually sold on Amazon)
        source_type = "Local"    (data comes from local file, not live API)

    Usage:
        svc = LocalProductService()
        products = svc.search_products(requirements)
    """

    def __init__(self, products_path: Path = None):
        self._path    = products_path or PRODUCTS_PATH
        self._products = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_products(self, requirements: dict) -> list[dict]:
        """
        Filter products.json by category and budget.

        Args:
            requirements: { "category": str, "budget": float, "features": list }

        Returns:
            List of product dicts tagged source="Amazon", source_type="Local".
        """
        raw_category = requirements.get("category", "").lower().strip()
        budget       = float(requirements.get("budget", 0))
        category     = _CATEGORY_ALIASES.get(raw_category, raw_category)

        results = []
        for p in self._products:
            pc  = p.get("category", "").lower()
            pcr = _CATEGORY_ALIASES.get(pc, pc)
            car = _CATEGORY_ALIASES.get(category, category)

            # Category filter
            if category and car not in pcr and pcr not in car:
                continue

            # Budget filter (0 = no limit)
            if budget > 0 and p.get("price", 0) > budget:
                continue

            results.append(dict(p))   # return a copy

        logger.info(
            "[LocalProductService] category=%r budget=%s → %d products",
            category, budget, len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> list[dict]:
        if not self._path.exists():
            logger.warning("[LocalProductService] %s not found — returning empty list", self._path)
            return []

        with open(self._path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Normalise schema and tag every product
        normalised = []
        for i, p in enumerate(raw):
            normalised.append({
                "id":          p.get("id",       f"local-{i:03d}"),
                "name":        p.get("name",      "Unknown"),
                "price":       float(p.get("price", 0)),
                "category":    p.get("category",  ""),
                "camera":      p.get("camera",    "N/A"),
                "battery":     p.get("battery",   "N/A"),
                "brand":       p.get("brand",     ""),
                "rating":      float(p.get("rating", 0.0)),
                "source":      "Amazon",     # conceptually listed on Amazon
                "source_type": "Local",      # actual data from local file
            })
        return normalised
