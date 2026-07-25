"""
Demo Chatbot Endpoint for Immediate Testing

Provides a sample RAG chatbot endpoint so users can test the evaluation pipeline out-of-the-box.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

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

    Accepts questions and returns simulated answers with retrieved document contexts.
    """
    start = time.perf_counter()
    user_query = request.query or request.question or request.message or ""
    query_lower = user_query.lower()

    if "loan" in query_lower or "ltv" in query_lower or "finance" in query_lower:
        answer = "According to 2026 commercial loan guidelines, the maximum loan-to-value (LTV) ratio for commercial property is 75%, provided the Debt Service Coverage Ratio (DSCR) is at least 1.25x."
        contexts = [
            {"content": "Commercial lending policy 2026: LTV capped at 75% for commercial real estate.", "source": "Policy_Doc_2026.pdf", "score": 0.95},
            {"content": "Minimum DSCR requirement is 1.25x for all commercial term loans.", "source": "Underwriting_Guidelines.pdf", "score": 0.89},
        ]
    elif "hipaa" in query_lower or "medical" in query_lower or "patient" in query_lower:
        answer = "Under HIPAA privacy rules, Protected Health Information (PHI) must be encrypted both in transit (TLS 1.3) and at rest (AES-256). Business Associate Agreements (BAA) are required for all third-party AI processors."
        contexts = [
            {"content": "HIPAA Privacy Rule 45 CFR Part 160: Administrative and physical safeguards required for electronic PHI.", "source": "HIPAA_Compliance_Manual.pdf", "score": 0.98},
        ]
    elif "ignore" in query_lower or "system prompt" in query_lower or "dan" in query_lower:
        answer = "I cannot fulfill this request. I am bound by strict security and compliance guardrails."
        contexts = []
    else:
        answer = f"Based on our internal knowledge base regarding '{user_query}', our system operates strictly in compliance with enterprise standards and data retention guidelines."
        contexts = [
            {"content": f"Enterprise knowledge base entry relating to: {user_query}", "source": "Enterprise_KB_Main.pdf", "score": 0.82},
        ]

    latency = (time.perf_counter() - start) * 1000

    return DemoChatbotResponse(
        answer=answer,
        contexts=contexts,
        model="demo-rag-v1",
        latency_ms=round(latency, 2),
    )
