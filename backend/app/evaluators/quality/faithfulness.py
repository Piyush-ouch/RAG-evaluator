"""
Faithfulness Evaluator

Measures how faithful the response is to the retrieved context.
A faithful response only contains information from the context,
without adding unsupported information.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class FaithfulnessEvaluator(BaseEvaluator):
    """
    Measures how faithful the response is to the retrieved context.

    A faithful response only contains information from the context,
    without adding unsupported information.
    """

    name = "faithfulness"
    description = "Measures answer-context alignment"
    version = "1.0"

    STOP_WORDS = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "not", "with", "this", "that",
        "it", "its", "as", "by", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "can", "shall", "from", "up", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
    })

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="Missing response or context.",
            )

        response_words = set(context.response_text.lower().split())
        context_words = set(" ".join(context.retrieved_chunks).lower().split())

        response_content = response_words - self.STOP_WORDS
        context_content = context_words - self.STOP_WORDS

        if not response_content:
            return EvaluationScore(
                evaluator_type=self.name, score=1.0,
                explanation="No content words in response.",
            )

        overlap = response_content & context_content
        faithfulness = len(overlap) / len(response_content)
        score = min(faithfulness * 1.2, 1.0)  # Slight boost since some paraphrasing is expected

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.6,
            explanation=f"{len(overlap)}/{len(response_content)} content words found in context.",
            details={"overlap_words": len(overlap), "response_words": len(response_content)},
        )
