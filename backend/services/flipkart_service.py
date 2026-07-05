"""
flipkart_service.py
-------------------
Simulated Flipkart product catalogue service.

Architecture note:
  This is a SERVICE layer module — it knows about data and filtering
  but has no knowledge of agents, routes, or AI.

  The static catalogue here can be replaced with Flipkart's Affiliate API
  (or any REST client) without changing any agent or orchestrator code.

Responsibilities:
  - Maintain a simulated Flipkart product catalogue
  - Filter products by category and budget
  - Tag every product with source="Flipkart"
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simulated Flipkart product catalogue
# ---------------------------------------------------------------------------
FLIPKART_CATALOGUE: list[dict] = [
    # ── Smartphones ────────────────────────────────────────────────
    {
        "id": "fk-sp-001", "source": "Flipkart",
        "name": "Vivo V29e 5G", "brand": "Vivo",
        "price": 22999, "category": "smartphone", "rating": 4.3,
        "camera": "50MP good camera", "battery": "4800mAh",
    },
    {
        "id": "fk-sp-002", "source": "Flipkart",
        "name": "Tecno Spark 20 Pro+", "brand": "Tecno",
        "price": 13999, "category": "smartphone", "rating": 4.1,
        "camera": "108MP good camera", "battery": "5000mAh",
    },
    {
        "id": "fk-sp-003", "source": "Flipkart",
        "name": "Infinix Note 40 Pro", "brand": "Infinix",
        "price": 19999, "category": "smartphone", "rating": 4.2,
        "camera": "108MP good camera", "battery": "5000mAh",
    },
    {
        "id": "fk-sp-004", "source": "Flipkart",
        "name": "Poco M6 Pro 5G", "brand": "Poco",
        "price": 14999, "category": "smartphone", "rating": 4.3,
        "camera": "50MP good camera", "battery": "5000mAh",
    },
    {
        "id": "fk-sp-005", "source": "Flipkart",
        "name": "Samsung Galaxy F55 5G", "brand": "Samsung",
        "price": 26999, "category": "smartphone", "rating": 4.2,
        "camera": "50MP good camera", "battery": "5000mAh",
    },
    # ── Laptops ───────────────────────────────────────────────────
    {
        "id": "fk-lp-001", "source": "Flipkart",
        "name": "Acer Aspire Lite", "brand": "Acer",
        "price": 41999, "category": "laptop", "rating": 4.0,
        "camera": "720p webcam", "battery": "48Whr",
    },
    {
        "id": "fk-lp-002", "source": "Flipkart",
        "name": "HP 15s-eq3038AU", "brand": "HP",
        "price": 47999, "category": "laptop", "rating": 4.2,
        "camera": "720p webcam", "battery": "41Whr",
    },
    {
        "id": "fk-lp-003", "source": "Flipkart",
        "name": "Dell Inspiron 3511", "brand": "Dell",
        "price": 52999, "category": "laptop", "rating": 4.3,
        "camera": "720p webcam", "battery": "42Whr",
    },
    # ── Headphones ─────────────────────────────────────────────────
    {
        "id": "fk-hp-001", "source": "Flipkart",
        "name": "boAt Rockerz 551 ANC", "brand": "boAt",
        "price": 2999, "category": "headphones", "rating": 4.1,
        "camera": "N/A", "battery": "60 hours playback",
    },
    {
        "id": "fk-hp-002", "source": "Flipkart",
        "name": "Noise One ANC", "brand": "Noise",
        "price": 3499, "category": "headphones", "rating": 4.0,
        "camera": "N/A", "battery": "40 hours playback",
    },
    # ── Smartwatches ───────────────────────────────────────────────
    {
        "id": "fk-sw-001", "source": "Flipkart",
        "name": "Noise ColorFit Ultra 3", "brand": "Noise",
        "price": 3499, "category": "smartwatch", "rating": 4.1,
        "camera": "N/A", "battery": "7-day battery life",
    },
    {
        "id": "fk-sw-002", "source": "Flipkart",
        "name": "Fire-Boltt Ninja Call Pro Plus", "brand": "Fire-Boltt",
        "price": 2499, "category": "smartwatch", "rating": 3.9,
        "camera": "N/A", "battery": "7-day battery life",
    },
    # ── Tablets ────────────────────────────────────────────────────
    {
        "id": "fk-tb-001", "source": "Flipkart",
        "name": "Realme Pad 2", "brand": "Realme",
        "price": 16999, "category": "tablet", "rating": 4.1,
        "camera": "8MP camera", "battery": "6860mAh",
    },
]

# ---------------------------------------------------------------------------
# Category alias map
# ---------------------------------------------------------------------------
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


class FlipkartService:
    """
    Simulates Flipkart product search.

    In production, replace _fetch_products() with an actual
    Flipkart Affiliate API call.

    Usage:
        svc = FlipkartService()
        products = svc.search_products(requirements)
    """

    def search_products(self, requirements: dict) -> list[dict]:
        """
        Search for Flipkart products matching the given requirements.

        Args:
            requirements: {
                "category": str,
                "budget":   float,
                "features": list[str]
            }

        Returns:
            List of product dicts, each tagged with source="Flipkart".
        """
        raw_category = requirements.get("category", "").lower().strip()
        budget       = float(requirements.get("budget", 0))

        category = _CATEGORY_ALIASES.get(raw_category, raw_category)

        results = self._fetch_products(category, budget)
        logger.info(
            "[FlipkartService] category=%r budget=%s → %d products",
            category, budget, len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_products(self, category: str, budget: float) -> list[dict]:
        """
        Retrieve matching products from the catalogue.

        Replace this method body with a real HTTP call to Flipkart's API
        without touching any agent or orchestrator code.
        """
        results = []
        for p in FLIPKART_CATALOGUE:
            pc = _CATEGORY_ALIASES.get(p.get("category", "").lower(), p.get("category", "").lower())

            # Category filter
            if category:
                cat = _CATEGORY_ALIASES.get(category, category)
                if cat not in pc and pc not in cat:
                    continue

            # Budget filter (0 = no limit)
            if budget > 0 and p.get("price", 0) > budget:
                continue

            results.append(dict(p))

        return results
