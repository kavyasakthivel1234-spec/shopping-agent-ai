"""
pros_cons_service.py
--------------------
Generates AI-powered pros and cons for a single product.

Architecture position:
    GroqService  ←  called by this service
    ProsConsService ←  called by routes

This service is responsible for:
  - Looking up a product by ID from the catalogue
  - Delegating the AI call to GroqService
  - Returning a clean pros/cons dict

It has no knowledge of HTTP or response serialisation.
"""

import json
from pathlib import Path

PRODUCTS_PATH = Path(__file__).parent.parent / "products.json"


class ProsConsService:
    """
    Produces AI-generated pros and cons for a given product.

    Usage:
        service = ProsConsService(groq_service)
        result  = service.generate_pros_cons("sp-001")
    """

    def __init__(self, groq_service):
        """
        Args:
            groq_service: An initialised GroqService instance.
        """
        self.groq_service = groq_service
        self.products: list[dict] = self._load_products()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pros_cons(self, product_id: str) -> dict:
        """
        Generate pros and cons for the product identified by product_id.

        Args:
            product_id: The "id" field from products.json (e.g. "sp-001").

        Returns:
            {
                "product_id"  : "sp-001",
                "product_name": "Samsung Galaxy M35",
                "pros"        : ["Excellent battery life", ...],
                "cons"        : ["Average charging speed", ...]
            }

        Raises:
            KeyError:    If no product with the given ID exists.
            RuntimeError/ValueError: Propagated from GroqService on AI failure.
        """
        product = self._find_product(product_id)

        # Delegate AI generation to GroqService
        result = self.groq_service.generate_pros_cons(product)

        return {
            "product_id":   product["id"],
            "product_name": product["name"],
            "pros":         result["pros"],
            "cons":         result["cons"],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_products(self) -> list[dict]:
        """Load the product catalogue from products.json."""
        if not PRODUCTS_PATH.exists():
            raise FileNotFoundError(
                f"Product catalogue not found at: {PRODUCTS_PATH}"
            )
        with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _find_product(self, product_id: str) -> dict:
        """
        Return the product dict for the given ID.

        Raises:
            KeyError: If the product_id does not exist in the catalogue.
        """
        for product in self.products:
            if product["id"] == product_id:
                return product
        raise KeyError(f"Product '{product_id}' not found in catalogue.")
