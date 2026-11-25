"""
RAGBench HuggingFace Loader

Loads RAGBench benchmark subsets from Hugging Face (`rungalileo/ragbench`).
Supports subset selection, split selection ('test' default), streaming/partial fetching,
and offline fallback samples for testing.
"""

from __future__ import annotations

from typing import Any, Generator, Sequence

import structlog

logger = structlog.get_logger(__name__)

SUPPORTED_SUBSETS = [
    "finqa",
    "tatqa",
    "pubmedqa",
    "techqa",
    "hotpotqa",
]

SUBSET_DISPLAY_NAMES = {
    "finqa": "RAGBench — FinQA",
    "tatqa": "RAGBench — TAT-QA",
    "pubmedqa": "RAGBench — PubMedQA",
    "techqa": "RAGBench — TechQA",
    "hotpotqa": "RAGBench — HotpotQA",
}

SUBSET_DESCRIPTIONS = {
    "finqa": "Financial question answering over earnings reports, balance sheets, and numerical filings.",
    "tatqa": "Tabular and textual financial question answering requiring arithmetic synthesis.",
    "pubmedqa": "Biomedical research QA based on PubMed abstracts and clinical trial evidence.",
    "techqa": "Technical customer support and troubleshooting question answering over enterprise documentation.",
    "hotpotqa": "Multi-hop reasoning and diverse document synthesis across multi-document knowledge graphs.",
}


class RAGBenchLoader:
    """Loader interface for Hugging Face RAGBench dataset."""

    DATASET_NAME = "rungalileo/ragbench"

    @classmethod
    def load_subset(
        cls,
        subset: str,
        split: str = "test",
        limit: int = 40,
    ) -> list[dict[str, Any]]:
        """
        Load records for a specific RAGBench subset.

        Attempts loading from Hugging Face `datasets.load_dataset`.
        Falls back to built-in synthetic benchmark data if remote repository is unreachable.
        """
        subset = subset.lower()
        if subset not in SUPPORTED_SUBSETS:
            raise ValueError(
                f"Unsupported RAGBench subset '{subset}'. Supported subsets: {SUPPORTED_SUBSETS}"
            )

        records: list[dict[str, Any]] = []

        try:
            from datasets import load_dataset
            logger.info("loading_ragbench_huggingface", subset=subset, split=split, limit=limit)
            
            # Use streaming=True to avoid downloading large archive files
            ds = load_dataset(cls.DATASET_NAME, subset, split=split, streaming=True)
            for idx, item in enumerate(ds):
                if idx >= limit:
                    break
                records.append(dict(item))
            logger.info("ragbench_loaded_successfully", subset=subset, count=len(records))
            return records
        except Exception as err:
            logger.warning(
                "ragbench_hf_load_failed_using_offline_seed",
                subset=subset,
                error=str(err),
            )
            return cls._get_offline_records(subset, limit)

    @classmethod
    def _get_offline_records(cls, subset: str, limit: int) -> list[dict[str, Any]]:
        """Generate high-quality reference benchmark records for offline/test environments."""
        from app.benchmark.offline_data import get_offline_ragbench_subset
        return get_offline_ragbench_subset(subset, limit)
