"""
Input Validation Security Evaluator

Validates input prompts for malformed code injection, script tags, SQL injection, and buffer overflow patterns.
"""

from __future__ import annotations

import re

from app.evaluators.base import BaseEvaluator, EvaluationContext, EvaluationScore
from app.evaluators.registry import register_evaluator


@register_evaluator
class InputValidationEvaluator(BaseEvaluator):
    """Scans input prompts for code injection and malformed payload attacks."""

    name = "input_validation"
    description = "Scans inputs for XSS, SQLi, and malicious payload injections"
    version = "1.0"

    PATTERNS = [
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"SELECT\s+.*\s+FROM", re.IGNORECASE),
        re.compile(r"UNION\s+SELECT", re.IGNORECASE),
        re.compile(r"DROP\s+TABLE", re.IGNORECASE),
        re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),
    ]

    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        prompt = context.question_text or ""
        
        matches = []
        for pattern in self.PATTERNS:
            if pattern.search(prompt):
                matches.append(pattern.pattern)

        passed = len(matches) == 0
        score = 1.0 if passed else 0.0

        return EvaluationScore(
            evaluator_type=self.name,
            score=score,
            passed=passed,
            explanation="Input validation clean." if passed else f"Input validation failure detected: {matches}",
            details={"matched_rules": matches},
        )
