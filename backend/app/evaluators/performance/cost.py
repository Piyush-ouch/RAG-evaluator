"""
Cost Evaluator

Evaluates token usage and estimated cost efficiency.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class CostEvaluator(BaseEvaluator):
    """Evaluates token usage and estimated cost."""

    name = "cost"
    description = "Token usage and cost analysis"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        total_tokens = context.total_tokens or (context.input_tokens + context.output_tokens)

        # Score based on token efficiency (lower is better)
        if total_tokens <= 500:
            score = 1.0
        elif total_tokens <= 2000:
            score = 1.0 - ((total_tokens - 500) / 1500) * 0.5
        elif total_tokens <= 5000:
            score = 0.5 - ((total_tokens - 2000) / 3000) * 0.3
        else:
            score = max(0.0, 0.2 - ((total_tokens - 5000) / 10000) * 0.2)

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=True,  # Cost is informational, not pass/fail
            explanation=f"Tokens: {total_tokens} (in={context.input_tokens}, out={context.output_tokens})",
            details={
                "total_tokens": total_tokens,
                "input_tokens": context.input_tokens,
                "output_tokens": context.output_tokens,
            },
        )
