"""
Benchmark Dataset Ingestion Engine

Parses and validates benchmark datasets in CSV, JSON, and Excel formats.
Supports ground truth answers, expected contexts, categories, tags, and difficulty levels.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Sequence

from pydantic import BaseModel, Field


class BenchmarkQuestionItem(BaseModel):
    """Parsed benchmark question item schema."""
    text: str = Field(..., description="Prompt question text")
    expected_answer: str | None = Field(None, description="Ground truth target answer")
    expected_context: list[str] = Field(default_factory=list, description="Ground truth context chunks")
    category: str = Field("general", description="Domain category tag")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")
    difficulty: str = Field("medium", description="Difficulty level (easy, medium, hard)")


class DatasetParser:
    """Ingestion engine for CSV, JSON, and Excel benchmark datasets."""

    @classmethod
    def parse_csv(cls, content: bytes | str) -> list[BenchmarkQuestionItem]:
        """Parse CSV dataset file content into structured question items."""
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        reader = csv.DictReader(io.StringIO(text))
        
        items = []
        for row in reader:
            q_text = row.get("question") or row.get("text") or row.get("prompt")
            if not q_text:
                continue
            
            exp_context = []
            ctx_val = row.get("expected_context") or row.get("context")
            if ctx_val:
                exp_context = [c.strip() for c in ctx_val.split(";") if c.strip()]

            tags = []
            tags_val = row.get("tags")
            if tags_val:
                tags = [t.strip() for t in tags_val.split(",") if t.strip()]

            items.append(BenchmarkQuestionItem(
                text=q_text.strip(),
                expected_answer=(row.get("expected_answer") or row.get("answer") or "").strip() or None,
                expected_context=exp_context,
                category=(row.get("category") or "general").strip(),
                tags=tags,
                difficulty=(row.get("difficulty") or "medium").strip(),
            ))
        return items

    @classmethod
    def parse_json(cls, content: bytes | str) -> list[BenchmarkQuestionItem]:
        """Parse JSON dataset file content into structured question items."""
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        data = json.loads(text)
        
        raw_items = data if isinstance(data, list) else data.get("questions", [])
        items = []
        for item in raw_items:
            q_text = item.get("question") or item.get("text") or item.get("prompt")
            if not q_text:
                continue

            exp_ctx = item.get("expected_context") or item.get("context") or []
            if isinstance(exp_ctx, str):
                exp_ctx = [exp_ctx]

            items.append(BenchmarkQuestionItem(
                text=q_text.strip(),
                expected_answer=item.get("expected_answer") or item.get("answer"),
                expected_context=exp_ctx,
                category=item.get("category", "general"),
                tags=item.get("tags", []),
                difficulty=item.get("difficulty", "medium"),
            ))
        return items
