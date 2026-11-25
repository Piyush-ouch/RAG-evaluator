"""
RAGBench Import Service

Coordinates:
Dataset Loading -> Normalization -> Validation -> Deduplication -> Persistence
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.benchmark.deduplicator import QuestionDeduplicator
from app.benchmark.normalizer import RAGBenchNormalizer, SUBSET_CATEGORY_MAP
from app.benchmark.ragbench import (
    RAGBenchLoader,
    SUBSET_DESCRIPTIONS,
    SUBSET_DISPLAY_NAMES,
    SUPPORTED_SUBSETS,
)
from app.benchmark.repository import BenchmarkRepository
from app.benchmark.validator import QuestionValidator

logger = structlog.get_logger(__name__)


class RAGBenchImportService:
    """Service governing high-quality benchmark dataset imports from RAGBench into PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BenchmarkRepository(session)

    async def import_subset(
        self,
        subset: str,
        split: str = "test",
        limit: int = 40,
        org_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Import a specific subset of RAGBench idempotently.

        Returns statistics:
        {
            "subset": "finqa",
            "inserted": 40,
            "skipped": 0,
            "duplicates": 0,
            "invalid": 0,
            "suite_id": "...",
            "suite_name": "RAGBench — FinQA",
            "total_questions": 40
        }
        """
        subset = subset.lower()
        if subset not in SUPPORTED_SUBSETS:
            raise ValueError(f"Unknown subset '{subset}'. Supported: {SUPPORTED_SUBSETS}")

        # 1. Resolve Project and Org
        if not project_id:
            project = await self.repo.get_or_create_default_project(org_id)
            project_id = project.id
            org_id = project.org_id

        # 2. Get or create Benchmark Suite
        suite_name = SUBSET_DISPLAY_NAMES.get(subset, f"RAGBench — {subset.upper()}")
        suite_desc = SUBSET_DESCRIPTIONS.get(subset, f"RAGBench {subset} evaluation test set.")
        domain = SUBSET_CATEGORY_MAP.get(subset, "general")

        suite = await self.repo.get_or_create_ragbench_suite(
            project_id=project_id,
            org_id=org_id,
            name=suite_name,
            domain=domain,
            description=suite_desc,
            subset=subset,
            version="1.0",
        )

        # 3. Load raw records from RAGBench
        raw_items = RAGBenchLoader.load_subset(subset=subset, split=split, limit=limit)

        # 4. Initialize Deduplicator with existing database questions
        existing_keys = await self.repo.get_existing_question_identity_keys(suite.id)
        deduplicator = QuestionDeduplicator(existing_keys)

        inserted_count = 0
        duplicate_count = 0
        invalid_count = 0
        skipped_count = 0

        current_order = suite.question_count

        for idx, raw_item in enumerate(raw_items):
            # Normalization
            canonical = RAGBenchNormalizer.normalize_record(
                raw_item=raw_item,
                subset=subset,
                index=idx,
                dataset_version="1.0",
            )

            # Validation
            is_valid, reason = QuestionValidator.validate(canonical)
            if not is_valid:
                logger.warning("benchmark_question_invalid", reason=reason, idx=idx, subset=subset)
                invalid_count += 1
                continue

            # Deduplication
            if deduplicator.is_duplicate(canonical):
                duplicate_count += 1
                continue

            # Persistence
            await self.repo.insert_question(
                suite_id=suite.id,
                q=canonical,
                order_index=current_order + inserted_count,
            )
            inserted_count += 1

        await self.session.flush()

        # Update total count in suite
        final_question_count = await self.repo.update_suite_question_count(suite.id)
        await self.session.commit()

        logger.info(
            "ragbench_subset_import_complete",
            subset=subset,
            inserted=inserted_count,
            duplicates=duplicate_count,
            invalid=invalid_count,
            total=final_question_count,
        )

        return {
            "subset": subset,
            "suite_id": str(suite.id),
            "suite_name": suite.name,
            "inserted": inserted_count,
            "skipped": skipped_count,
            "duplicates": duplicate_count,
            "invalid": invalid_count,
            "total_questions": final_question_count,
        }

    async def import_all_subsets(
        self,
        subsets: list[str] | None = None,
        split: str = "test",
        limit_per_subset: int = 40,
        org_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Import all requested RAGBench subsets sequentially."""
        target_subsets = subsets or SUPPORTED_SUBSETS
        results = []
        total_inserted = 0
        total_duplicates = 0
        total_invalid = 0
        total_skipped = 0

        for sub in target_subsets:
            res = await self.import_subset(
                subset=sub,
                split=split,
                limit=limit_per_subset,
                org_id=org_id,
                project_id=project_id,
            )
            results.append(res)
            total_inserted += res["inserted"]
            total_duplicates += res["duplicates"]
            total_invalid += res["invalid"]
            total_skipped += res["skipped"]

        return {
            "dataset": "ragbench",
            "subsets": results,
            "total_inserted": total_inserted,
            "total_duplicates": total_duplicates,
            "total_invalid": total_invalid,
            "total_skipped": total_skipped,
        }
