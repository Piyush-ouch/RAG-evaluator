"""
Context Relevance Evaluator

Measures how relevant the retrieved context chunks are to the input question.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class ContextRelevanceEvaluator(BaseEvaluator):
    """Measures context relevance relative to the prompt question."""

    name = "context_relevance"
    description = "Measures question-context semantic relevance"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.question_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                passed=False,
                explanation="Missing input question or retrieved context chunks.",
            )

        q_words = set(context.question_text.lower().split())
        c_text = " ".join(context.retrieved_chunks).lower()
        
        matches = sum(1 for w in q_words if w in c_text)
        relevance = min(matches / max(len(q_words), 1) * 1.5, 1.0)

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(relevance, 3),
            passed=relevance >= 0.6,
            explanation=f"Context relevance score: {round(relevance, 3)} based on keyword presence.",
            details={"matched_keywords": matches, "total_prompt_terms": len(q_words)},
        )
