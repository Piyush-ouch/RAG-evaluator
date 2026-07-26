"""
Latency Evaluator

Evaluates response latency against configurable thresholds.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class LatencyEvaluator(BaseEvaluator):
    """Evaluates response latency against thresholds."""

    name = "latency"
    description = "Response time analysis"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        latency = context.latency_ms

        # Score: 1.0 for <1s, linear decay to 0 at 10s
        if latency <= 1000:
            score = 1.0
        elif latency <= 10000:
            score = 1.0 - ((latency - 1000) / 9000)
        else:
            score = 0.0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=latency <= 5000,
            explanation=f"Response time: {latency:.0f}ms",
            details={"latency_ms": latency},
        )
