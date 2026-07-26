"""
Context Recall Evaluator

Measures recall of expected context in retrieved chunks.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class ContextRecallEvaluator(BaseEvaluator):
    """Measures recall of expected context in retrieved chunks."""

    name = "context_recall"
    description = "Recall of expected contexts"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.expected_context:
            return EvaluationScore(
                evaluator_type=self.name, score=0.5,
                explanation="No expected context defined.",
            )

        if not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="No retrieved chunks.",
            )

        retrieved_text = " ".join(context.retrieved_chunks).lower()
        found = 0
        for expected in context.expected_context:
            # Check if key info from expected context appears in retrieved
            key_words = [w for w in expected.lower().split() if len(w) > 4]
            if key_words:
                match_ratio = sum(1 for w in key_words if w in retrieved_text) / len(key_words)
                if match_ratio >= 0.3:
                    found += 1

        recall = found / len(context.expected_context) if context.expected_context else 0
        return EvaluationScore(
            evaluator_type=self.name,
            score=round(recall, 3),
            passed=recall >= 0.5,
            explanation=f"{found}/{len(context.expected_context)} expected contexts found.",
        )
