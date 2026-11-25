"""
Completeness Evaluator

Measures if the generated answer thoroughly covers all parts of the question or expected ground truth.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class CompletenessEvaluator(BaseEvaluator):
    """Measures answer completeness relative to expected answers or retrieved context."""

    name = "completeness"
    description = "Measures response coverage and detail completeness"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                passed=False,
                explanation="Response text is empty.",
            )

        resp_len = len(context.response_text.split())
        if resp_len < 5:
            score = 0.2
        elif resp_len < 15:
            score = 0.6
        else:
            score = 1.0

        if context.expected_answer:
            exp_terms = set(w for w in context.expected_answer.lower().split() if len(w) > 3)
            if exp_terms:
                found = sum(1 for t in exp_terms if t in context.response_text.lower())
                score = min(found / len(exp_terms), 1.0)

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.6,
            explanation=f"Answer completeness score: {round(score, 3)}.",
            details={"response_word_count": resp_len},
        )
