"""
Quality Evaluators — Hallucination, Faithfulness, Correctness

These evaluators assess the quality of RAG responses by comparing
the generated answer against the expected answer and retrieved context.
"""

from __future__ import annotations

import re

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class HallucinationDetector(BaseEvaluator):
    """
    Detects hallucinated content — claims not grounded in the retrieved context.

    Uses heuristic analysis:
    1. Extracts factual claims from the response
    2. Checks if each claim is supported by retrieved context
    3. Score = 1.0 - (hallucinated_claims / total_claims)
    """

    name = "hallucination"
    description = "Detects claims not grounded in the retrieved context"
    version = "1.0"

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                explanation="No response or context to evaluate.",
            )

        response_lower = context.response_text.lower()
        context_text = " ".join(context.retrieved_chunks).lower()

        # Extract sentences as claim proxies
        sentences = [s.strip() for s in re.split(r'[.!?]+', context.response_text) if len(s.strip()) > 10]

        if not sentences:
            return EvaluationScore(
                evaluator_type=self.name, score=1.0,
                explanation="No factual claims detected.",
            )

        grounded = 0
        ungrounded_claims = []
        for sentence in sentences:
            # Check if key content words appear in context
            words = [w for w in sentence.lower().split() if len(w) > 3]
            if not words:
                grounded += 1
                continue
            overlap = sum(1 for w in words if w in context_text)
            overlap_ratio = overlap / len(words) if words else 0

            if overlap_ratio >= 0.3:  # At least 30% word overlap
                grounded += 1
            else:
                ungrounded_claims.append(sentence[:100])

        score = grounded / len(sentences) if sentences else 1.0

        return EvaluationScore(
            evaluator_type=self.name,
            score=round(score, 3),
            passed=score >= 0.7,
            explanation=f"{grounded}/{len(sentences)} claims grounded in context.",
            details={
                "total_claims": len(sentences),
                "grounded_claims": grounded,
                "ungrounded_claims": ungrounded_claims[:5],
            },
        )


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

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name, score=0.0,
                explanation="Missing response or context.",
            )

        response_words = set(context.response_text.lower().split())
        context_words = set(" ".join(context.retrieved_chunks).lower().split())

        # Remove stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                      "to", "for", "of", "and", "or", "but", "not", "with", "this", "that",
                      "it", "its", "as", "by", "be", "been", "being", "have", "has", "had",
                      "do", "does", "did", "will", "would", "could", "should", "may", "might",
                      "can", "shall", "from", "up", "about", "into", "through", "during",
                      "before", "after", "above", "below", "between", "out", "off", "over"}
        response_content = response_words - stop_words
        context_content = context_words - stop_words

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
