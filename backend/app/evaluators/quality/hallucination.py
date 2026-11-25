"""
Hallucination Detector

Detects hallucinated content — claims, numbers, and factual anchors not grounded
in the retrieved context, and generates an explicit root-cause explanation of
WHY the response hallucinated.
"""

from __future__ import annotations

import re

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class HallucinationDetector(BaseEvaluator):
    """
    Detects hallucinated content — claims not grounded in the retrieved context —
    and produces a detailed root-cause diagnosis explaining why it hallucinated.
    """

    name = "hallucination"
    description = "Detects claims not grounded in the retrieved context and explains why"
    version = "2.0"

    STOP_WORDS = frozenset({
        "the", "and", "for", "that", "this", "with", "from", "were", "was",
        "are", "have", "has", "had", "not", "but", "what", "which", "when",
        "where", "who", "will", "would", "could", "should", "into", "about",
        "than", "then", "them", "they", "their", "there", "been", "being",
        "only", "also", "more", "most", "some", "such", "very", "just",
        "based", "according", "grounded", "source", "context",
    })

    NUMBER_PATTERN = re.compile(r"\b\d+(?:,\d{3})*(?:\.\d+)?%?\b")

    GENERIC_BOILERPLATE_MARKERS = [
        "operates strictly in compliance with enterprise standards and data retention guidelines",
        "provided no source document",
        "please specify the company",
        "please specify the organization",
        "without knowing the specific",
        "currently do not have access to the data",
    ]

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        if not context.response_text or not context.retrieved_chunks:
            return EvaluationScore(
                evaluator_type=self.name,
                score=0.0,
                passed=False,
                explanation="Hallucinated / Ungrounded: Missing chatbot response or no retrieved context chunks were returned by the retriever.",
                details={
                    "hallucination_reason": "No retrieved context chunks were returned to ground the response.",
                    "total_claims": 0,
                    "grounded_claims": 0,
                    "ungrounded_claims": [],
                    "unverified_numbers": [],
                    "unsupported_terms": [],
                },
            )

        context_text = " ".join(context.retrieved_chunks).lower()
        response_lower = context.response_text.lower()

        # Check for generic evasion / missing-context boilerplate
        for marker in self.GENERIC_BOILERPLATE_MARKERS:
            if marker in response_lower:
                reason = (
                    f"Chatbot failed to ground its answer in the benchmark document and emitted generic/evasive "
                    f"text ('{marker}') instead of retrieving factual evidence from the source passage."
                )
                return EvaluationScore(
                    evaluator_type=self.name,
                    score=0.35,
                    passed=False,
                    explanation=reason,
                    details={
                        "hallucination_reason": reason,
                        "total_claims": 1,
                        "grounded_claims": 0,
                        "ungrounded_claims": [context.response_text[:140]],
                        "unverified_numbers": [],
                        "unsupported_terms": [marker],
                    },
                )

        # Extract sentences as atomic factual claims
        sentences = [
            s.strip()
            for s in re.split(r"[.!?]+", context.response_text)
            if len(s.strip()) > 10
        ]

        if not sentences:
            return EvaluationScore(
                evaluator_type=self.name,
                score=1.0,
                passed=True,
                explanation="0% Hallucination — Response is concise and contains no ungrounded factual claims.",
                details={
                    "hallucination_reason": "No ungrounded factual claims detected.",
                    "total_claims": 0,
                    "grounded_claims": 0,
                    "ungrounded_claims": [],
                    "unverified_numbers": [],
                    "unsupported_terms": [],
                },
            )

        grounded = 0
        ungrounded_claims: list[str] = []
        claim_diagnostics: list[str] = []
        all_unsupported_terms: list[str] = []

        for sentence in sentences:
            words = [
                re.sub(r"[^a-z0-9%.]", "", w)
                for w in sentence.lower().split()
            ]
            content_words = [
                w for w in words
                if len(w) > 3 and w not in self.STOP_WORDS
            ]
            if not content_words:
                grounded += 1
                continue

            supported = [w for w in content_words if w in context_text]
            unsupported = [w for w in content_words if w not in context_text]
            overlap_ratio = len(supported) / len(content_words)

            if overlap_ratio >= 0.30:
                grounded += 1
            else:
                snippet = sentence[:120] + ("..." if len(sentence) > 120 else "")
                ungrounded_claims.append(snippet)
                missing_sample = ", ".join(unsupported[:5])
                claim_diagnostics.append(
                    f"Claim \"{snippet}\" had only {round(overlap_ratio * 100)}% context support "
                    f"(unsupported terms: {missing_sample})"
                )
                for term in unsupported[:4]:
                    if term not in all_unsupported_terms:
                        all_unsupported_terms.append(term)

        # Check numeric anchors (numbers/percentages in response that aren't in retrieved context)
        response_numbers = self.NUMBER_PATTERN.findall(context.response_text)
        unverified_numbers = [
            num for num in response_numbers
            if num not in context_text and num.replace(",", "") not in context_text
        ]

        base_score = grounded / len(sentences) if sentences else 1.0
        # Penalize slightly if unverified numbers were fabricated outside context
        numeric_penalty = min(0.25, len(unverified_numbers) * 0.08) if unverified_numbers and base_score < 1.0 else 0.0
        score = max(0.0, round(base_score - numeric_penalty, 3))

        # Build explicit human-readable "Why it hallucinated" reason
        reasons: list[str] = []
        if ungrounded_claims:
            reasons.append(
                f"{len(ungrounded_claims)} of {len(sentences)} claim(s) lacked sufficient lexical grounding (<30% token overlap) in the retrieved chunks: "
                + "; ".join(claim_diagnostics[:2])
            )
        if unverified_numbers:
            reasons.append(
                f"Response introduced unverified numeric values ({', '.join(unverified_numbers[:4])}) not present in the retrieved source context."
            )
        if not reasons:
            if score >= 0.99:
                reasons.append(
                    f"0% Hallucination — All {grounded}/{len(sentences)} factual claims and numeric anchors were directly verified in the retrieved context chunks."
                )
            else:
                reasons.append(
                    f"Partial Grounding — {grounded}/{len(sentences)} claims verified in context."
                )

        hallucination_reason = " ".join(reasons)

        return EvaluationScore(
            evaluator_type=self.name,
            score=score,
            passed=score >= 0.7,
            explanation=hallucination_reason,
            details={
                "hallucination_reason": hallucination_reason,
                "total_claims": len(sentences),
                "grounded_claims": grounded,
                "ungrounded_claims": ungrounded_claims[:5],
                "unverified_numbers": unverified_numbers[:6],
                "unsupported_terms": all_unsupported_terms[:8],
            },
        )
