"""
Evaluation Pipeline

Orchestrates the end-to-end evaluation flow:
1. Load questions from benchmark suite
2. Call customer's chatbot API for each question
3. Capture response + context + metadata
4. Run all enabled evaluators in parallel
5. Store results in database
6. Compute aggregated metrics
7. Trigger report generation
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

from app.evaluators.base import EvaluationContext, EvaluationScore
from app.evaluators.registry import get_evaluator

logger = structlog.get_logger(__name__)


class EvaluationPipeline:
    """
    Orchestrator for running evaluations.

    Stateless — all state is in the database. The pipeline fetches
    questions, calls the chatbot, runs evaluators, and stores results.
    """

    def __init__(
        self,
        chatbot_url: str,
        chatbot_method: str = "POST",
        chatbot_headers: dict[str, str] | None = None,
        chatbot_request_template: dict | None = None,
        chatbot_response_path: str | None = None,
        enabled_evaluators: list[str] | None = None,
        concurrency: int = 5,
    ):
        self.chatbot_url = chatbot_url
        self.chatbot_method = chatbot_method
        self.chatbot_headers = chatbot_headers or {"Content-Type": "application/json"}
        self.chatbot_request_template = chatbot_request_template
        self.chatbot_response_path = chatbot_response_path
        self.enabled_evaluators = enabled_evaluators or []
        self.concurrency = concurrency

    async def call_chatbot(
        self,
        question: str,
        expected_context: list[str] | None = None,
        expected_answer: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a question to the customer's chatbot API.

        Returns the full response with timing metadata.
        """
        # Build request body from template or default
        if self.chatbot_request_template:
            body = {**self.chatbot_request_template}
            # Replace {{question}} placeholder
            for key, value in body.items():
                if isinstance(value, str) and "{{question}}" in value:
                    body[key] = value.replace("{{question}}", question)
        else:
            body = {
                "query": question,
                "question": question,
                "message": question,
                "contexts": expected_context or [],
                "expected_answer": expected_answer,
            }

        # Resolve URL for Docker network if calling backend container internally or host machine
        urls_to_try = [self.chatbot_url]
        if "localhost:8000" in self.chatbot_url:
            urls_to_try.insert(0, self.chatbot_url.replace("localhost:8000", "backend:8000"))
        elif "127.0.0.1:8000" in self.chatbot_url:
            urls_to_try.insert(0, self.chatbot_url.replace("127.0.0.1:8000", "backend:8000"))
        elif "localhost:" in self.chatbot_url:
            urls_to_try.append(self.chatbot_url.replace("localhost:", "host.docker.internal:"))
        elif "127.0.0.1:" in self.chatbot_url:
            urls_to_try.append(self.chatbot_url.replace("127.0.0.1:", "host.docker.internal:"))

        start_time = time.perf_counter()
        last_error = None

        for target_url in urls_to_try:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.request(
                        method=self.chatbot_method,
                        url=target_url,
                        json=body,
                        headers=self.chatbot_headers,
                    )
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    if response.is_success:
                        response_data = response.json()
                        response_text = self._extract_response(response_data)
                        chunks = self._extract_chunks(response_data)

                        return {
                            "response_text": response_text,
                            "response_raw": response_data,
                            "retrieved_chunks": chunks,
                            "latency_ms": latency_ms,
                            "status_code": response.status_code,
                        }
            except Exception as e:
                last_error = str(e)

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error("chatbot_call_failed", error=last_error)
        return {
            "response_text": None,
            "response_raw": {"error": last_error},
            "retrieved_chunks": [],
            "latency_ms": latency_ms,
            "status_code": 0,
            "error": last_error,
        }

    def _extract_response(self, data: dict) -> str | None:
        """Extract the response text from the chatbot's response."""
        if self.chatbot_response_path:
            # Simple dot-path extraction (e.g., "data.answer")
            parts = self.chatbot_response_path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return str(current) if current else None

        # Default: try common response field names
        for field in ["answer", "response", "text", "content", "message",
                      "result", "output", "reply", "data"]:
            if field in data:
                val = data[field]
                if isinstance(val, str):
                    return val
                if isinstance(val, dict):
                    for sub in ["text", "content", "answer", "message"]:
                        if sub in val:
                            return str(val[sub])
        return str(data)

    def _extract_chunks(self, data: dict) -> list[dict]:
        """Extract retrieved context chunks from the response."""
        for field in ["contexts", "chunks", "sources", "retrieved_documents",
                      "context", "references", "documents"]:
            if field in data and isinstance(data[field], list):
                return [
                    {
                        "content": item.get("content", item.get("text", str(item))),
                        "source": item.get("source", item.get("url", "")),
                        "score": item.get("score", item.get("relevance_score", 0.0)),
                    }
                    for item in data[field]
                ]
        return []

    async def evaluate_question(
        self,
        question_text: str,
        expected_answer: str | None = None,
        expected_context: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate a single question — call chatbot, run evaluators.

        Returns all results for database storage.
        """
        # Step 1: Call chatbot
        chatbot_result = await self.call_chatbot(
            question_text,
            expected_context=expected_context,
            expected_answer=expected_answer,
        )

        # Step 2: Build evaluation context
        chunks = chatbot_result.get("retrieved_chunks", [])
        context = EvaluationContext(
            question_text=question_text,
            expected_answer=expected_answer,
            response_text=chatbot_result.get("response_text"),
            retrieved_chunks=[c.get("content", "") for c in chunks],
            chunk_sources=[c.get("source", "") for c in chunks],
            chunk_scores=[c.get("score", 0.0) for c in chunks],
            expected_context=expected_context or [],
            latency_ms=chatbot_result.get("latency_ms", 0),
        )

        # Step 3: Run evaluators in parallel
        scores: list[EvaluationScore] = []
        if self.enabled_evaluators and chatbot_result.get("response_text"):
            evaluator_tasks = []
            for evaluator_name in self.enabled_evaluators:
                try:
                    evaluator = get_evaluator(evaluator_name)
                    evaluator_tasks.append(evaluator.evaluate(context))
                except ValueError:
                    logger.warning("evaluator_not_found", name=evaluator_name)

            if evaluator_tasks:
                results = await asyncio.gather(*evaluator_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, EvaluationScore):
                        scores.append(result)
                    elif isinstance(result, Exception):
                        logger.error("evaluator_failed", error=str(result))

        # Step 4: Compute overall score
        overall_score = None
        if scores:
            overall_score = sum(s.score for s in scores) / len(scores)

        return {
            "chatbot_result": chatbot_result,
            "scores": scores,
            "overall_score": overall_score,
            "context": context,
        }
