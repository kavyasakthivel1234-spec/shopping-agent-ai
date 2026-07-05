"""
orchestrator.py
---------------
ShoppingAssistantOrchestrator

Architecture (Groq + SerpAPI only):

    User Query
          ↓
    Groq NLP (is_smalltalk / extract_requirements)
          ↓  [shopping]
    RequirementAgent   — Groq extracts structured filters
          ↓
    AmazonSearchAgent  — SerpAPI fetches REAL Amazon India products
          ↓
    RecommendationAgent — score + rank real products
          ↓
    ReviewAgent (optional) — Groq summarises reviews
          ↓
    Final Response

Rules:
    - ZERO mock data, ZERO Flipkart catalogue
    - Groq = NLP only
    - SerpAPI = real products only
"""

import logging

from agents.requirement_agent    import RequirementAgent
from agents.amazon_search_agent  import AmazonSearchAgent
from agents.recommendation_agent import RecommendationAgent
from agents.review_agent         import ReviewAgent
from agents.comparison_agent     import ComparisonAgent

from services.gemini_service   import GeminiService
from services.amazon_service   import AmazonService
from services.recommendation   import RecommendationService
from services.review_summary   import ReviewSummaryService
from services.comparison       import ComparisonService

logger = logging.getLogger(__name__)


class ShoppingAssistantOrchestrator:
    """
    Coordinates the Groq + SerpAPI pipeline.

    Groq handles all NLP. SerpAPI fetches all products.
    No Flipkart. No mock catalogues.
    """

    def __init__(
        self,
        gemini_service:         GeminiService         = None,
        amazon_service:         AmazonService         = None,
        recommendation_service: RecommendationService = None,
        review_summary_service: ReviewSummaryService  = None,
        comparison_service:     ComparisonService     = None,
    ):
        self._groq        = gemini_service         or GeminiService()
        self._amazon_svc  = amazon_service         or AmazonService()
        self._recommender = recommendation_service or RecommendationService()
        self._review_svc  = review_summary_service or ReviewSummaryService(self._groq)
        self._comparison  = comparison_service     or ComparisonService(self._groq)

        self.requirement_agent    = RequirementAgent(self._groq)
        self.amazon_agent         = AmazonSearchAgent(self._amazon_svc)
        self.recommendation_agent = RecommendationAgent(self._recommender)
        self.review_agent         = ReviewAgent(self._review_svc)
        self.comparison_agent     = ComparisonAgent(self._comparison)

    # ── Public API ──────────────────────────────────────────────────

    def process_query(self, query: str) -> dict:
        """
        Route the query and return a structured result.

        Returns one of:
          { pipeline_type: "smalltalk", chat_text, pipeline }
          { pipeline_type: "shopping",  requirements, top_pick, alternatives,
            review_summary, confidence, pipeline }
          { error, failed_agent, pipeline }
        """
        logger.info("[Orchestrator] Query: %r", query)

        # ── Smalltalk fast path ──────────────────────────────────
        if GeminiService.is_smalltalk(query):
            logger.info("[Orchestrator] Smalltalk detected")
            return {
                "pipeline_type": "smalltalk",
                "chat_text":     self._groq.chat_response(query),
                "pipeline":      ["SmallTalkHandler"],
            }

        pipeline: list[str] = []

        # ── Step 1: Groq extracts filters ────────────────────────
        req_result = self.requirement_agent.run(query)
        pipeline.append(self.requirement_agent.NAME)
        if req_result["status"] == "error":
            return self._error(req_result["error"], "RequirementAgent", pipeline)

        requirements = req_result["data"]
        print(f"[Orchestrator] Groq Extracted Filters: {requirements}")
        logger.info("[Orchestrator] Filters: %s", requirements)

        # ── Step 2: SerpAPI fetches real Amazon products ─────────
        amz_result   = self.amazon_agent.run(requirements)
        pipeline.append(self.amazon_agent.NAME)
        amz_products = amz_result["data"] if amz_result["status"] == "success" else []

        if amz_result["status"] == "error":
            logger.error("[Orchestrator] AmazonSearchAgent failed: %s", amz_result.get("error"))
            # If Amazon search itself fails (e.g. no API key), surface the error clearly
            return self._error(amz_result["error"], "AmazonSearchAgent", pipeline)

        print(f"[Orchestrator] SerpAPI returned {len(amz_products)} products")

        # ── Step 3: Rank real products ────────────────────────────
        rec_result = self.recommendation_agent.run(
            requirements,
            product_pool = amz_products,
        )
        pipeline.append(self.recommendation_agent.NAME)
        if rec_result["status"] == "error":
            return self._error(rec_result["error"], "RecommendationAgent", pipeline)

        rec_data     = rec_result["data"]
        top_pick     = rec_data.get("top_pick")
        alternatives = rec_data.get("alternatives", [])
        confidence   = rec_data.get("confidence", 0.0)

        # ── Step 4: Groq summarises reviews (non-fatal) ───────────
        review_summary = None
        if top_pick:
            rev = self.review_agent.run(top_pick["id"])
            pipeline.append(self.review_agent.NAME)
            if rev["status"] == "success":
                review_summary = rev["data"]
            else:
                logger.warning("[Orchestrator] ReviewAgent failed (non-fatal): %s", rev.get("error"))

        logger.info(
            "[Orchestrator] Done | pipeline=%s | top=%s | confidence=%.2f",
            pipeline,
            top_pick["name"] if top_pick else "None",
            confidence,
        )

        return {
            "pipeline_type":  "shopping",
            "requirements":   requirements,
            "top_pick":       top_pick,
            "alternatives":   alternatives,
            "review_summary": review_summary,
            "confidence":     confidence,
            "pipeline":       pipeline,
        }

    def compare(self, product1_id: str, product2_id: str) -> dict:
        result = self.comparison_agent.run(product1_id, product2_id)
        if result["status"] == "error":
            return {"error": result["error"], "failed_agent": "ComparisonAgent"}
        return result["data"]

    # ── Private ──────────────────────────────────────────────────────

    def _error(self, message: str, failed_agent: str, pipeline: list) -> dict:
        return {"error": message, "failed_agent": failed_agent, "pipeline": pipeline}
