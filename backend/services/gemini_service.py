"""
gemini_service.py
-----------------
Backwards-compatibility shim.

All AI functionality has been migrated to Groq (Llama 3.3 70B).
This file re-exports GeminiService from groq_service so that existing
imports across agents, routes, and the orchestrator continue to work
without modification.

Every file that does:
    from services.gemini_service import GeminiService
will now get the Groq-backed implementation.
"""

from services.groq_service import GeminiService  # noqa: F401

__all__ = ["GeminiService"]
