"""
intent_router.py
-----------------
Agent responsible for routing user queries to the appropriate processing flow.

Detects:
  - Greetings (exact phrase match)
  - Shopping queries (keyword and phrase match, excluding general comparisons)
  - Product comparison requests (explicit reference to recommended products or shopping entities + comparison intent)
  - General chat (anything else)
"""

import re

class IntentRouter:
    """
    Classifies natural language queries to determine the correct execution pipeline.
    """

    @staticmethod
    def is_greeting(query: str) -> bool:
        """
        Check if the query is an exact match for a greeting keyword/phrase
        after trimming and lowercasing.
        """
        clean = re.sub(r'[^\w\s]', '', query).strip().lower()
        greetings = {
            "hi", "hello", "hey", "good morning", "good evening",
            "how are you", "who are you", "thank you", "thanks"
        }
        return clean in greetings

    @staticmethod
    def is_shopping_query(query: str) -> bool:
        """
        Check if the query is a shopping request based on keywords, comparison intents, or phrases.
        """
        query_lc = query.strip().lower()

        # 1. Direct Keyword Matching (excluding comparison keywords for now)
        shopping_keywords = {
            "phone", "mobile", "smartphone", "laptop", "headphone", "earbuds",
            "watch", "smartwatch", "tablet", "camera", "buy", "purchase",
            "budget", "recommend", "price", "shopping"
        }
        words = set(re.findall(r'\b\w+\b', query_lc))
        if not words.isdisjoint(shopping_keywords):
            return True

        # 2. Check for product comparison intent
        if "compare" in query_lc or "vs" in query_lc or "versus" in query_lc:
            if IntentRouter.is_product_comparison_intent(query_lc):
                return True

        # 3. Phrase-based matching
        # "under 50000" / "below 30k" etc.
        if re.search(r'\b(under|below|budget|price|cost|₹|rs)\s*\d+\b', query_lc):
            return True
        if re.search(r'\b\d+\s*(k|k rupees|rupees|inr)\b', query_lc):
            return True

        # "best laptop" / "best phone" / "best smartwatch" etc.
        categories = [
            "laptop", "phone", "mobile", "smartphone", "headphone",
            "earbuds", "watch", "smartwatch", "tablet", "camera"
        ]
        categories_pattern = "|".join(categories)
        if re.search(rf'\bbest\s+({categories_pattern})\b', query_lc):
            return True

        # "recommend a phone" / "recommend a laptop"
        if re.search(rf'\brecommend\s+(a|an|the|some)?\s*({categories_pattern})\b', query_lc):
            return True

        # "which mobile should I buy"
        if re.search(rf'\bwhich\s+({categories_pattern})\s+(\w+\s+){{0,3}}buy\b', query_lc):
            return True

        return False

    @staticmethod
    def is_product_comparison_intent(query_lc: str) -> bool:
        """
        Determines if a query containing comparison terms is actually asking to compare products.
        """
        # Ensure it has comparison terms
        has_compare_keyword = any(w in query_lc for w in ["compare", "vs", "versus"])
        if not has_compare_keyword:
            return False

        # References to previously recommended products
        refs = [
            "first", "second", "1st", "2nd", "them", "both", "laptops",
            "phones", "devices", "models", "options", "picks",
            "recommendations", "product"
        ]
        has_ref = any(r in query_lc for r in refs)

        # Shopping entities
        shopping_entities = {
            "phone", "mobile", "smartphone", "laptop", "headphone", "earbuds",
            "watch", "smartwatch", "tablet", "camera", "device", "model", "brand",
            "samsung", "apple", "lenovo", "hp", "asus", "oneplus", "sony", "boat"
        }
        words = set(re.findall(r'\b\w+\b', query_lc))
        has_shopping_entity = not words.isdisjoint(shopping_entities)

        return has_ref or has_shopping_entity

    @staticmethod
    def is_general_chat(query: str) -> bool:
        """
        Returns True if the query is neither a greeting nor a shopping query.
        """
        return not IntentRouter.is_greeting(query) and not IntentRouter.is_shopping_query(query)


# Predefined greeting responses
GREETING_RESPONSES = {
    "hi": (
        "Hello.\n"
        "I'm your AI Shopping Assistant.\n"
        "I can help you with product recommendations and general questions.\n"
        "What would you like to do today?"
    ),
    "hello": (
        "Hello.\n"
        "I'm your AI Shopping Assistant.\n"
        "I can help you with product recommendations and general questions.\n"
        "What would you like to do today?"
    ),
    "hey": (
        "Hello.\n"
        "I'm your AI Shopping Assistant.\n"
        "I can help you with product recommendations and general questions.\n"
        "What would you like to do today?"
    ),
    "good morning": (
        "Hello.\n"
        "I'm your AI Shopping Assistant.\n"
        "I can help you with product recommendations and general questions.\n"
        "What would you like to do today?"
    ),
    "good evening": (
        "Hello.\n"
        "I'm your AI Shopping Assistant.\n"
        "I can help you with product recommendations and general questions.\n"
        "What would you like to do today?"
    ),
    "how are you": (
        "I'm doing great.\n"
        "Ready to help you with shopping or answer your questions."
    ),
    "who are you": (
        "I'm an AI Shopping Assistant powered by Llama 3.\n"
        "I can chat normally and also recommend products based on your requirements."
    ),
    "thank you": (
        "You're welcome. Let me know if you need help with anything else."
    ),
    "thanks": (
        "You're welcome. Let me know if you need help with anything else."
    )
}
