"""
Groundedness Evaluator

Measures how well the response is grounded in source documents.
Distinct from Faithfulness: checks factual anchoring via named entities,
numbers, and domain-specific terminology rather than raw word overlap.
"""

from __future__ import annotations

import re

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class GroundednessEvaluator(BaseEvaluator):
    """
    Measures factual anchoring of the response in retrieved context.

    Extracts factual anchors (numbers, percentages, named entities,
    domain terms) from the response and checks how many appear
    in the retrieved context.
    """

    name = "groundedness"
    description = "Measures factual anchoring in source documents"
    version = "1.0"

    # Patterns for factual anchors
    NUMBER_PATTERN = re.compile(r'\b\d+(?:\.\d+)?%?\b')
    PROPER_NOUN_PATTERN = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="Missing response or context.",
            )

        context_text = " ".join(context.retrieved_chunks)
        context_lower = context_text.lower()

        # Extract factual anchors from response
        response_numbers = set(self.NUMBER_PATTERN.findall(context.response_text))
        response_entities = set(self.PROPER_NOUN_PATTERN.findall(context.response_text))
        # Domain terms: words > 6 chars that are likely technical
        response_terms = {
            w for w in context.response_text.lower().split()
            if len(w) > 6 and w.isalpha()
        }

        all_anchors = response_numbers | {e.lower() for e in response_entities} | response_terms

        if not all_anchors:
            return EvaluationScore(
                evaluator_type=self.name, score=1.0,
                explanation="No factual anchors to verify.",
            )

        grounded = sum(1 for anchor in all_anchors if anchor.lower() in context_lower)
        score = grounded / len(all_anchors) if all_anchors else 1.0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.6,
            explanation=f"{grounded}/{len(all_anchors)} factual anchors grounded in context.",
            details={
                "total_anchors": len(all_anchors),
                "grounded_anchors": grounded,
                "numbers_found": len(response_numbers),
                "entities_found": len(response_entities),
                "terms_found": len(response_terms),
            },
        )
