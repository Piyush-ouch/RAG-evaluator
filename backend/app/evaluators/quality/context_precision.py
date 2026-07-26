"""
Context Precision Evaluator

Measures precision of retrieved context chunks against expected context.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class ContextPrecisionEvaluator(BaseEvaluator):
    """Measures precision of retrieved context chunks."""

    name = "context_precision"
    description = "Precision of retrieved contexts vs expected"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="No retrieved chunks.",
            )

        if not context.expected_context:
            # Without ground truth, use chunk relevance scores
            if context.chunk_scores:
                avg_score = sum(context.chunk_scores) / len(context.chunk_scores)
                return EvaluationScore(
                    evaluator_type=self.name, score=round(avg_score, 3),
                    explanation=f"Average chunk relevance: {avg_score:.3f}",
                )
            return EvaluationScore(
                evaluator_type=self.name, score=0.5,
                explanation="No expected context or scores available.",
            )

        # Compare retrieved vs expected
        expected_set = set(" ".join(context.expected_context).lower().split())
        relevant_chunks = 0
        for chunk in context.retrieved_chunks:
            chunk_words = set(chunk.lower().split())
            overlap = len(chunk_words & expected_set) / len(chunk_words) if chunk_words else 0
            if overlap >= 0.2:
                relevant_chunks += 1

        precision = relevant_chunks / len(context.retrieved_chunks)
        return EvaluationScore(
            evaluator_type=self.name,
            score=round(precision, 3),
            passed=precision >= 0.5,
            explanation=f"{relevant_chunks}/{len(context.retrieved_chunks)} chunks relevant.",
        )
