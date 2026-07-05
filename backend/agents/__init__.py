"""
agents/
-------
Multi-agent layer for the AI Shopping Assistant (Phase 3).

Each agent is a focused, single-responsibility unit that:
  - Accepts a well-defined input
  - Calls one or more services (never business logic directly)
  - Returns a normalised result envelope: { agent, status, data | error }

Agents are coordinated by the ShoppingAssistantOrchestrator.

Exports
-------
RequirementAgent     — parse raw user query → structured requirements
RecommendationAgent  — filter + score products → top_pick + alternatives
ReviewAgent          — summarise product reviews → liked / disliked
ComparisonAgent      — AI side-by-side product comparison
ShoppingAssistantOrchestrator — wires all agents into one workflow
"""

from agents.requirement_agent import RequirementAgent
from agents.recommendation_agent import RecommendationAgent
from agents.review_agent import ReviewAgent
from agents.comparison_agent import ComparisonAgent
from agents.orchestrator import ShoppingAssistantOrchestrator
from agents.intent_router import IntentRouter, GREETING_RESPONSES

__all__ = [
    "RequirementAgent",
    "RecommendationAgent",
    "ReviewAgent",
    "ComparisonAgent",
    "ShoppingAssistantOrchestrator",
    "IntentRouter",
    "GREETING_RESPONSES",
]
