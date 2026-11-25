"""
RAGBench Question Deduplicator

Ensures idempotent imports by tracking and filtering questions with stable identity:
(source_dataset, source_subset, source_question_id, dataset_version).
"""

from __future__ import annotations

from typing import Set

from app.benchmark.normalizer import CanonicalQuestion


class QuestionDeduplicator:
    """Detects and deduplicates questions within import batches and against database records."""

    @staticmethod
    def get_identity_key(
        source_dataset: str,
        source_subset: str,
        source_question_id: str,
        dataset_version: str = "1.0",
    ) -> str:
        """Construct the canonical compound unique key for a benchmark question."""
        return f"{source_dataset.strip().lower()}::{source_subset.strip().lower()}::{source_question_id.strip()}::{dataset_version.strip()}"

    @classmethod
    def get_question_key(cls, item: CanonicalQuestion) -> str:
        """Construct compound unique key from a CanonicalQuestion instance."""
        return cls.get_identity_key(
            source_dataset=item.source_dataset,
            source_subset=item.source_subset,
            source_question_id=item.source_question_id,
            dataset_version=item.dataset_version,
        )

    def __init__(self, existing_keys: Set[str] | None = None):
        self._seen_keys: Set[str] = set(existing_keys or [])

    def is_duplicate(self, item: CanonicalQuestion) -> bool:
        """Check if item has already been seen or persisted."""
        key = self.get_question_key(item)
        if key in self._seen_keys:
            return True
        self._seen_keys.add(key)
        return False
