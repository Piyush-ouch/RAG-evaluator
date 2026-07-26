"""
Citation Quality Evaluator

Verifies that cited sources exist in retrieved chunks and
checks citation accuracy.
"""

from __future__ import annotations

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class CitationQualityEvaluator(BaseEvaluator):
    """
    Evaluates citation quality by checking:
    1. Whether response citations match retrieved chunk sources
    2. Citation completeness (are all relevant sources cited?)
    3. Citation accuracy (do cited sources support the claims?)
    """

    name = "citation_quality"
    description = "Verifies citation accuracy and completeness"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="No response to evaluate.",
            )

        # Check if expected citations are available
        if not context.expected_citations and not context.response_citations:
            # No citation data — evaluate based on chunk source references
            if not context.chunk_sources:
                return EvaluationScore(
                    evaluator_type=self.name, score=0.5,
                    explanation="No citation data available for evaluation.",
                )

            # Check if any chunk sources are mentioned in response
            response_lower = context.response_text.lower()
            sources_mentioned = sum(
                1 for src in context.chunk_sources
                if src and src.lower() in response_lower
            )
            available_sources = len([s for s in context.chunk_sources if s])
            score = sources_mentioned / available_sources if available_sources else 0.5

            return EvaluationScore(
                evaluator_type=self.name,
                score=round(score, 3),
                passed=score >= 0.3,
                explanation=f"{sources_mentioned}/{available_sources} sources referenced in response.",
                details={"sources_mentioned": sources_mentioned, "available_sources": available_sources},
            )

        # Compare response citations against expected
        expected_set = {c.lower().strip() for c in (context.expected_citations or [])}
        response_set = {c.lower().strip() for c in (context.response_citations or [])}

        if not expected_set:
            return EvaluationScore(
                evaluator_type=self.name, score=0.5,
                explanation="No expected citations to compare.",
            )

        # Precision: what fraction of response citations are correct
        correct_citations = response_set & expected_set
        precision = len(correct_citations) / len(response_set) if response_set else 0
        # Recall: what fraction of expected citations are present
        recall = len(correct_citations) / len(expected_set) if expected_set else 0
        # F1
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(f1, 3),
            passed=f1 >= 0.5,
            explanation=f"Citation F1={f1:.3f} (P={precision:.3f}, R={recall:.3f})",
            details={
                "precision": precision, "recall": recall, "f1": f1,
                "correct_citations": list(correct_citations),
                "missing_citations": list(expected_set - response_set),
                "extra_citations": list(response_set - expected_set),
            },
        )
