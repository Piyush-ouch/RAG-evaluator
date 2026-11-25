"""
RAGBench Canonical Normalizer

Converts raw records from RAGBench subsets into the project's canonical Question format.
Decouples internal application models from upstream benchmark schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalQuestion:
    """Canonical internal question schema for benchmark evaluation."""
    question: str
    expected_answer: str | None
    expected_context: list[str] = field(default_factory=list)
    category: str = "general"
    subcategory: str | None = None
    difficulty: str = "medium"
    evaluation_type: str = "rag"
    tags: list[str] = field(default_factory=list)
    source_dataset: str = "ragbench"
    source_subset: str = "general"
    source_question_id: str = ""
    dataset_version: str = "1.0"
    is_active: bool = True
    metadata_json: dict[str, Any] = field(default_factory=dict)


# Mapping of RAGBench subsets to high-level domain categories
SUBSET_CATEGORY_MAP: dict[str, str] = {
    "finqa": "finance",
    "tatqa": "finance",
    "pubmedqa": "healthcare",
    "techqa": "technical",
    "hotpotqa": "multi-hop",
    "covidqa": "healthcare",
    "cuad": "legal",
    "msmarco": "search",
}


class RAGBenchNormalizer:
    """Normalizes raw RAGBench dataset rows into CanonicalQuestion instances."""

    @classmethod
    def normalize_record(
        cls,
        raw_item: dict[str, Any],
        subset: str,
        index: int,
        dataset_version: str = "1.0",
    ) -> CanonicalQuestion:
        """
        Normalize a raw dictionary from RAGBench into a CanonicalQuestion.

        Handles varied column names across HuggingFace RAGBench subsets:
        - question / query / prompt / text
        - response / answer / ground_truth / expected_answer
        - documents / context / contexts
        - id / question_id / item_id
        """
        # 1. Question Text
        question_text = (
            raw_item.get("question")
            or raw_item.get("query")
            or raw_item.get("prompt")
            or raw_item.get("text")
            or ""
        )
        if isinstance(question_text, (list, tuple)):
            question_text = " ".join(str(q) for q in question_text)
        question_text = str(question_text).strip()

        # 2. Expected Answer (Ground Truth)
        # In RAGBench, 'response' contains the generated answer being evaluated or reference answer.
        expected_answer = (
            raw_item.get("expected_answer")
            or raw_item.get("ground_truth")
            or raw_item.get("answer")
            or raw_item.get("response")
        )
        if expected_answer is not None:
            if isinstance(expected_answer, (list, tuple)):
                expected_answer = " ".join(str(a) for a in expected_answer)
            expected_answer = str(expected_answer).strip()

        # 3. Expected Context (Reference documents / chunks)
        expected_context: list[str] = []
        raw_docs = (
            raw_item.get("documents")
            or raw_item.get("context")
            or raw_item.get("contexts")
            or []
        )
        if isinstance(raw_docs, str):
            try:
                parsed = json.loads(raw_docs)
                if isinstance(parsed, list):
                    raw_docs = parsed
                else:
                    raw_docs = [raw_docs]
            except Exception:
                raw_docs = [raw_docs]

        if isinstance(raw_docs, (list, tuple)):
            for doc in raw_docs:
                if isinstance(doc, dict):
                    text = doc.get("text") or doc.get("content") or doc.get("document") or ""
                    if text:
                        expected_context.append(str(text).strip())
                elif doc:
                    expected_context.append(str(doc).strip())

        # 4. Source Question ID
        source_id = str(
            raw_item.get("id")
            or raw_item.get("question_id")
            or raw_item.get("item_id")
            or f"{subset}_{index}"
        ).strip()

        # 5. Domain Category & Subcategory
        category = SUBSET_CATEGORY_MAP.get(subset.lower(), "general")
        subcategory = subset.lower()

        # 6. Tags
        tags = ["ragbench", subset.lower(), category]

        # 7. Metadata preservation (retain any analytical annotations, e.g. TRACe labels)
        preserved_meta = {}
        for k, v in raw_item.items():
            if k not in {"question", "query", "prompt", "documents", "context"}:
                try:
                    json.dumps(v)
                    preserved_meta[k] = v
                except (TypeError, ValueError):
                    preserved_meta[k] = str(v)

        return CanonicalQuestion(
            question=question_text,
            expected_answer=expected_answer,
            expected_context=expected_context,
            category=category,
            subcategory=subcategory,
            difficulty=raw_item.get("difficulty", "medium"),
            evaluation_type="rag",
            tags=tags,
            source_dataset="ragbench",
            source_subset=subset.lower(),
            source_question_id=source_id,
            dataset_version=dataset_version,
            is_active=True,
            metadata_json=preserved_meta,
        )
