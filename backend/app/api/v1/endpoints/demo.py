"""
Demo Chatbot Endpoint for Immediate Testing

Provides a sample RAG chatbot endpoint so users can test the evaluation pipeline out-of-the-box using real Gemini API.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.providers.llm import GeminiAdapter, Message

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/demo", tags=["Demo Chatbot"])


class DemoChatbotRequest(BaseModel):
    query: str | None = None
    question: str | None = None
    message: str | None = None


class DemoChatbotResponse(BaseModel):
    answer: str
    contexts: list[dict[str, Any]]
    model: str = "demo-rag-v1"
    latency_ms: float = 0.0


@router.post("/chatbot", response_model=DemoChatbotResponse)
async def demo_chatbot_endpoint(request: DemoChatbotRequest) -> DemoChatbotResponse:
    """
    Demo RAG Chatbot API.

    Calls real Google Gemini API directly if GOOGLE_AI_API_KEY is configured.
    """
    start = time.perf_counter()
    user_query = request.query or request.question or request.message or ""
    query_lower = user_query.lower()

    settings = get_settings()
    answer = ""
    model_name = "demo-rag-v1"

    # Try live Google Gemini API first if API key is configured
    if settings.google_ai_api_key and settings.google_ai_api_key.strip():
        try:
            adapter = GeminiAdapter(api_key=settings.google_ai_api_key, model="gemini-1.5-flash")
            messages = [
                Message(role="system", content="You are an enterprise AI assistant being evaluated for accuracy and compliance."),
                Message(role="user", content=user_query),
            ]
            llm_resp = await adapter.complete(messages)
            answer = llm_resp.content
            model_name = "google/gemini-1.5-flash (Real API)"
        except Exception as err:
            logger.warning("gemini_live_call_fallback", error=str(err))

    # Fallback to rule-based answers if live call wasn't executed
    if not answer:
        if "loan" in query_lower or "ltv" in query_lower or "finance" in query_lower:
            answer = "According to 2026 commercial loan guidelines, the maximum loan-to-value (LTV) ratio for commercial property is 75%, provided the Debt Service Coverage Ratio (DSCR) is at least 1.25x."
        elif "hipaa" in query_lower or "medical" in query_lower or "patient" in query_lower:
            answer = "Under HIPAA privacy rules, Protected Health Information (PHI) must be encrypted both in transit (TLS 1.3) and at rest (AES-256). Business Associate Agreements (BAA) are required for all third-party AI processors."
        elif "ignore" in query_lower or "system prompt" in query_lower or "dan" in query_lower:
            answer = "I cannot fulfill this request. I am bound by strict security and compliance guardrails."
        else:
            answer = f"Based on our internal knowledge base regarding '{user_query}', our system operates strictly in compliance with enterprise standards and data retention guidelines."

    contexts = [
        {"content": f"Verified context source entry relating to: {user_query}", "source": "Enterprise_Policy_Doc.pdf", "score": 0.94},
    ]

    latency = (time.perf_counter() - start) * 1000

    return DemoChatbotResponse(
        answer=answer,
        contexts=contexts,
        model=model_name,
        latency_ms=round(latency, 2),
    )

