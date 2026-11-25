"""
RAGBench Question Validator

Validates normalized canonical questions against quality criteria:
- Ensures non-empty question text
- Verifies source identity
- Discards corrupted or malformed entries
- Ensures expected context is preserved as valid list of strings
"""

from __future__ import annotations

from typing import Tuple

from app.benchmark.normalizer import CanonicalQuestion


class QuestionValidator:
    """Validates CanonicalQuestion instances before persistence."""

    MIN_QUESTION_LENGTH = 5

    @classmethod
    def validate(cls, item: CanonicalQuestion) -> Tuple[bool, str | None]:
        """
        Validate a CanonicalQuestion.

        Returns:
            (is_valid, rejection_reason)
        """
        # 1. Non-empty question text
        if not item.question or not item.question.strip():
            return False, "Question text is empty."

        if len(item.question.strip()) < cls.MIN_QUESTION_LENGTH:
            return False, f"Question text is too short (< {cls.MIN_QUESTION_LENGTH} chars)."

        # 2. Source ID
        if not item.source_question_id:
            return False, "Missing source question identifier."

        # 3. Source metadata integrity
        if not item.source_dataset or not item.source_subset:
            return False, "Missing source dataset or subset provenance."

        # 4. Context preservation integrity check
        if item.expected_context is not None and not isinstance(item.expected_context, list):
            return False, "expected_context must be a list of strings if provided."

        return True, None
