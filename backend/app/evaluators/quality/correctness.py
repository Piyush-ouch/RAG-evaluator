"""
Correctness Evaluator

Compares the response against the expected/ground-truth answer
using token-level F1 score for similarity measurement.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class CorrectnessEvaluator(BaseEvaluator):
    """
    Compares the response against the expected/ground-truth answer.

    Uses token-level F1 score for similarity measurement.
    """

    name = "correctness"
    description = "Compares against expected answers (F1 score)"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.expected_answer or not context.response_text:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="Missing expected answer or response.",
            )

        expected_tokens = set(context.expected_answer.lower().split())
        response_tokens = set(context.response_text.lower().split())

        if not expected_tokens or not response_tokens:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="Empty token set.",
            )

        # Token-level F1
        true_positives = len(expected_tokens & response_tokens)
        precision = true_positives / len(response_tokens) if response_tokens else 0
        recall = true_positives / len(expected_tokens) if expected_tokens else 0

        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(f1, 3),
            passed=f1 >= 0.5,
            explanation=f"F1={f1:.3f} (P={precision:.3f}, R={recall:.3f})",
            details={"f1": f1, "precision": precision, "recall": recall},
        )
