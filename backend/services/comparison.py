"""
comparison.py
-------------
Side-by-side AI product comparison service.

Updated for multi-source:
  - Searches across local products.json, Amazon catalogue, and Flipkart
    catalogue so cross-platform comparisons work (e.g. Amazon laptop vs
    Flipkart laptop).
  - Source field is preserved and included in the comparison result.
"""

import json
import logging
from pathlib import Path

from services.amazon_service   import AMAZON_CATALOGUE
from services.flipkart_service import FLIPKART_CATALOGUE

logger = logging.getLogger(__name__)

PRODUCTS_PATH = Path(__file__).parent.parent / "products.json"


class ComparisonService:
    """
    Produces an AI-driven side-by-side comparison of two products.

    Searches local, Amazon, and Flipkart catalogues to find products by ID,
    enabling cross-platform comparisons.

    Usage:
        service = ComparisonService(groq_service)
        result  = service.compare_products("amz-sp-001", "fk-sp-001")
    """

    def __init__(self, groq_service):
        self.groq_service = groq_service
        # Build a unified lookup dict: id → product
        self._catalogue: dict[str, dict] = self._build_catalogue()
        logger.info(
            "[ComparisonService] Catalogue: %d products across all sources",
            len(self._catalogue),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare_products(self, product1_id: str, product2_id: str) -> dict:
        """
        Compare two products (from any source) and return an AI breakdown.

        Args:
            product1_id: Product ID (local, Amazon, or Flipkart)
            product2_id: Product ID (local, Amazon, or Flipkart)

        Returns:
            {
                "product1":   { full product dict with source },
                "product2":   { full product dict with source },
                "comparison": {
                    "camera":  { "product1": "…", "product2": "…" },
                    "battery": { "product1": "…", "product2": "…" },
                    "price":   { "product1": "…", "product2": "…" },
                    "winner":  "Product Name",
                    "summary": "One sentence."
                }
            }
        """
        product1 = self._find_product(product1_id)
        product2 = self._find_product(product2_id)

        comparison = self.groq_service.generate_comparison(product1, product2)

        return {
            "product1":   product1,
            "product2":   product2,
            "comparison": comparison,
        }

    def get_product_by_id(self, product_id: str) -> dict | None:
        """Return a product dict by ID, or None if not found."""
        return self._catalogue.get(product_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_catalogue(self) -> dict[str, dict]:
        """
        Build a unified id→product lookup from all three sources.
        Local products are loaded from products.json.
        Amazon and Flipkart products come from their respective service modules.
        """
        catalogue: dict[str, dict] = {}

        # Local products
        if PRODUCTS_PATH.exists():
            with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
                local = json.load(f)
            for p in local:
                p.setdefault("source", "Local")
                p.setdefault("brand",  "")
                p.setdefault("rating", 0.0)
                catalogue[p["id"]] = p

        # Amazon products
        for p in AMAZON_CATALOGUE:
            catalogue[p["id"]] = dict(p)

        # Flipkart products
        for p in FLIPKART_CATALOGUE:
            catalogue[p["id"]] = dict(p)

        return catalogue

    def _find_product(self, product_id: str) -> dict:
        """
        Find a product by ID across all sources.

        Raises:
            KeyError: If the product_id is not in any catalogue.
        """
        product = self._catalogue.get(product_id)
        if not product:
            raise KeyError(
                f"Product '{product_id}' not found in local, Amazon, or Flipkart catalogues."
            )
        return product
