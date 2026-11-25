"""
Answer Relevance Evaluator

Measures how directly the chatbot's generated answer addresses the input question.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class AnswerRelevanceEvaluator(BaseEvaluator):
    """Measures answer relevance to the input prompt question."""

    name = "answer_relevance"
    description = "Measures question-answer alignment"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.question_text or not context.response_text:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                passed=False,
                explanation="Missing question or response text.",
            )

        q_terms = set(w for w in context.question_text.lower().split() if len(w) > 3)
        ans_text = context.response_text.lower()
        
        if not q_terms:
            return EvaluationScore(evaluator_type=self.name, score=1.0, passed=True, explanation="Short prompt.")

        matches = sum(1 for term in q_terms if term in ans_text)
        score = min(matches / len(q_terms) * 1.3, 1.0)

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.5,
            explanation=f"Answer relevance score: {round(score, 3)} based on prompt key terms.",
            details={"matched_terms": matches, "total_terms": len(q_terms)},
        )
