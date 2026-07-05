"""
review_summary.py
-----------------
Mock review summarisation service.

Architecture position:
    GroqService          ←  called by this service
    ReviewSummaryService  ←  called by routes

Phase 2 uses a static review dataset stored in this file.
In a future phase this will be replaced by reviews fetched from a
real database or third-party API.

Responsibilities:
  - Provide static review data keyed by product ID
  - Delegate summarisation to GroqService
  - Return a liked/disliked topic breakdown
"""

from services.groq_service import GroqService

# ---------------------------------------------------------------------------
# Static review dataset
# In a production system these would come from a database.
# ---------------------------------------------------------------------------
MOCK_REVIEWS: dict[str, list[str]] = {
    "sp-001": [
        "Battery is amazing, lasts all day easily",
        "Camera quality is great for the price",
        "Charging is quite slow compared to competitors",
        "Build quality feels premium",
        "Software updates are timely",
    ],
    "sp-002": [
        "Battery life is decent but not outstanding",
        "Camera produces vibrant colours",
        "Phone heats up during gaming",
        "Good value for money",
        "Charging speed is average",
    ],
    "sp-003": [
        "Camera is the standout feature – very sharp photos",
        "Battery easily lasts a full day",
        "Display is bright and vivid",
        "Occasional software lags noticed",
        "Excellent performance for the price",
    ],
    "sp-004": [
        "Best camera in this price range",
        "Battery could be better",
        "Fast charging is a big plus",
        "Slightly expensive but worth it",
    ],
    "sp-005": [
        "Great battery backup",
        "Camera is decent for everyday use",
        "Clean software experience",
        "Feels slightly bulky",
    ],
    "sp-006": [
        "Good camera and clean Android",
        "Battery life is solid",
        "Build quality could be improved",
        "Smooth performance",
    ],
    "sp-007": [
        "Reliable battery life",
        "Camera is average",
        "Budget-friendly and dependable",
        "No fast charging support",
    ],
    "sp-008": [
        "Good for basic usage",
        "Battery is satisfactory",
        "Camera is basic but functional",
        "Best in the entry segment",
    ],
}

# Fallback reviews used when a product has no specific review data
DEFAULT_REVIEWS: list[str] = [
    "Product works as expected",
    "Battery life is acceptable",
    "Good value for the price",
]


class ReviewSummaryService:
    """
    Summarises user reviews for a product into liked and disliked topics
    using Gemini AI.

    Usage:
        service = ReviewSummaryService(groq_service)
        summary = service.summarise(product_id="sp-001")
    """

    def __init__(self, groq_service: GroqService):
        """
        Args:
            groq_service: An initialised GroqService instance.
        """
        self.groq_service = groq_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarise(self, product_id: str) -> dict:
        """
        Retrieve mock reviews for the given product and summarise them
        into liked/disliked topics via Gemini.

        Args:
            product_id: The "id" field from products.json (e.g. "sp-001").

        Returns:
            {
                "product_id": "sp-001",
                "review_count": 5,
                "liked":    ["Battery", "Camera", "Build Quality"],
                "disliked": ["Charging Speed"]
            }

        Raises:
            RuntimeError/ValueError: Propagated from GroqService on AI failure.
        """
        # Fetch reviews — fall back to default if no specific data exists
        reviews = MOCK_REVIEWS.get(product_id, DEFAULT_REVIEWS)

        # Delegate AI summarisation to GroqService
        summary = self.groq_service.summarise_reviews(reviews)

        return {
            "product_id":   product_id,
            "review_count": len(reviews),
            "liked":        summary["liked"],
            "disliked":     summary["disliked"],
        }
