"""
Hallucination Detector

Detects hallucinated content — claims not grounded in the retrieved context.
Uses heuristic analysis to extract factual claims and check if each claim
is supported by retrieved context.
"""

from __future__ import annotations

import re

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class HallucinationDetector(BaseEvaluator):
    """
    Detects hallucinated content — claims not grounded in the retrieved context.

    Uses heuristic analysis:
    1. Extracts factual claims from the response
    2. Checks if each claim is supported by retrieved context
    3. Score = 1.0 - (hallucinated_claims / total_claims)
    """

    name = "hallucination"
    description = "Detects claims not grounded in the retrieved context"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                explanation="No response or context to evaluate.",
            )

        context_text = " ".join(context.retrieved_chunks).lower()

        # Extract sentences as claim proxies
        sentences = [
            s.strip()
            for s in re.split(r'[.!?]+', context.response_text)
            if len(s.strip()) > 10
        ]

        if not sentences:
            return EvaluationScore(
                evaluator_type=self.name, score=1.0,
                explanation="No factual claims detected.",
            )

        grounded = 0
        ungrounded_claims: list[str] = []
        for sentence in sentences:
            # Check if key content words appear in context
            words = [w for w in sentence.lower().split() if len(w) > 3]
            if not words:
                grounded += 1
                continue
            overlap = sum(1 for w in words if w in context_text)
            overlap_ratio = overlap / len(words) if words else 0

            if overlap_ratio >= 0.3:  # At least 30% word overlap
                grounded += 1
            else:
                ungrounded_claims.append(sentence[:100])

        score = grounded / len(sentences) if sentences else 1.0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.7,
            explanation=f"{grounded}/{len(sentences)} claims grounded in context.",
            details={
                "total_claims": len(sentences),
                "grounded_claims": grounded,
                "ungrounded_claims": ungrounded_claims[:5],
            },
        )
