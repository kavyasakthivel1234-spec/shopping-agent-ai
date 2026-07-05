"""
product_model.py
----------------
Pydantic models for the AI Shopping Assistant API.

All optional numeric fields (price, rating, reviews) can be None
because real Amazon/SerpAPI data frequently omits them.
The frontend must handle null and display "Not Available".
"""

from typing import Optional
from pydantic import BaseModel


# ============================================================================
# Core product model  (used by comparison, pros-cons routes)
# ============================================================================

class Product(BaseModel):
    id:           str
    name:         str
    price:        Optional[float] = None
    old_price:    Optional[float] = None    # original/strikethrough price
    category:     str             = ""
    camera:       str             = "N/A"
    battery:      str             = "N/A"
    # Source metadata
    source:       str             = "Amazon"
    source_type:  str             = "Real"
    data_mode:    str             = "amazon"
    # Real product fields — all nullable
    asin:         Optional[str]   = None
    brand:        Optional[str]   = None
    rating:       Optional[float] = None
    reviews:      Optional[int]   = None
    link:         Optional[str]   = None
    thumbnail:    Optional[str]   = None
    image:        Optional[str]   = None
    seller:       Optional[str]   = None
    availability: bool            = True
    bought_last_month: Optional[str] = None
    offers:       list            = []
    delivery:     list            = []


# ============================================================================
# Filter model (from Groq)
# ============================================================================

class ShoppingFilters(BaseModel):
    """Rich filter set extracted by Groq NLP from a user query."""
    product:     str            = ""
    brand:       Optional[str]  = None
    maxPrice:    Optional[float] = None
    minPrice:    Optional[float] = None
    minRating:   Optional[float] = None
    color:       Optional[str]  = None
    size:        Optional[str]  = None
    storage:     Optional[str]  = None
    ram:         Optional[str]  = None
    flavor:      Optional[str]  = None
    material:    Optional[str]  = None
    features:    list[str]      = []
    searchQuery: str            = ""
    # Legacy fields kept so orchestrator/recommendation service keep working
    category:       str         = ""
    budget:         float       = 0.0
    original_query: str         = ""


# ============================================================================
# Scored product (after ranking)
# ============================================================================

class ScoredProduct(BaseModel):
    id:           str
    name:         str
    price:        Optional[float] = None
    old_price:    Optional[float] = None    # strikethrough/original price
    category:     str             = ""
    camera:       str             = "N/A"
    battery:      str             = "N/A"
    score:        int             = 0
    # Source metadata
    source:       str             = "Amazon"
    source_type:  str             = "Real"
    data_mode:    str             = "amazon"
    # Real product fields — all nullable
    asin:         Optional[str]   = None
    brand:        Optional[str]   = None
    rating:       Optional[float] = None
    reviews:      Optional[int]   = None
    link:         Optional[str]   = None
    thumbnail:    Optional[str]   = None
    image:        Optional[str]   = None
    seller:       Optional[str]   = None
    availability: bool            = True
    bought_last_month: Optional[str] = None
    offers:       list            = []
    delivery:     list            = []


# ============================================================================
# Requirements (kept for legacy routes)
# ============================================================================

class Requirements(BaseModel):
    category: str       = ""
    budget:   float     = 0.0
    features: list[str] = []


class RecommendationRequest(BaseModel):
    query: str


class RecommendationResponse(BaseModel):
    requirements: Requirements
    top_pick:     Optional[ScoredProduct] = None
    alternatives: list[ScoredProduct]    = []


# ============================================================================
# Pros & cons
# ============================================================================

class ProsConsResponse(BaseModel):
    product_id:   str
    product_name: str
    pros:         list[str]
    cons:         list[str]


# ============================================================================
# Comparison
# ============================================================================

class CompareRequest(BaseModel):
    product1_id: str
    product2_id: str


class ComparisonDetail(BaseModel):
    product1: str
    product2: str


class ComparisonResult(BaseModel):
    camera:  ComparisonDetail
    battery: ComparisonDetail
    price:   ComparisonDetail
    winner:  str
    summary: str


class CompareResponse(BaseModel):
    product1:   Product
    product2:   Product
    comparison: ComparisonResult


# ============================================================================
# Review summary
# ============================================================================

class ReviewSummaryResponse(BaseModel):
    product_id:   str
    review_count: int
    liked:        list[str]
    disliked:     list[str]


# ============================================================================
# Assistant endpoint
# ============================================================================

class AssistantRequest(BaseModel):
    query: str


class AssistantResponse(BaseModel):
    requirements:   Requirements
    top_pick:       Optional[ScoredProduct] = None
    alternatives:   list[ScoredProduct]     = []
    review_summary: Optional[ReviewSummaryResponse] = None
    confidence:     float                   = 0.0
    pipeline:       list[str]               = []


# ============================================================================
# Legacy
# ============================================================================

class ProductRecommendationRequest(BaseModel):
    query: str


class ProductComparisonRequest(BaseModel):
    product_ids: list[str]
