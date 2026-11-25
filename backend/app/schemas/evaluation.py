"""
Evaluation & Benchmark Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Benchmark Suite
# ---------------------------------------------------------

class BenchmarkSuiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    domain: str = "general"


class BenchmarkSuiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    domain: str
    version: str
    question_count: int
    is_template: bool
    source_dataset: str | None = None
    source_subset: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1)
    expected_answer: str | None = None
    category: str | None = None
    difficulty: str = "medium"
    tags: list[str] = []
    expected_context: list[str] | None = None
    expected_citations: list[str] | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    text: str
    expected_answer: str | None = None
    category: str | None = None
    subcategory: str | None = None
    difficulty: str
    evaluation_type: str = "rag"
    order_index: int
    source_dataset: str | None = None
    source_subset: str | None = None
    source_question_id: str | None = None
    dataset_version: str = "1.0"
    tags: list = []
    expected_context: list[str] | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BenchmarkImportRequest(BaseModel):
    dataset: str = Field("ragbench", description="Dataset name, e.g. ragbench")
    subsets: list[str] = Field(default_factory=lambda: ["finqa", "tatqa", "pubmedqa", "techqa", "hotpotqa"])
    split: str = Field("test", description="Dataset split, default: test")
    limit_per_subset: int = Field(40, description="Max questions to import per subset")


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

class EvaluationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    suite_id: uuid.UUID
    description: str | None = None
    version_tag: str | None = None
    enabled_evaluators: list[str] = []


class EvaluationResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    version_tag: str | None = None
    total_questions: int
    completed_questions: int
    failed_questions: int
    overall_score: float | None = None
    accuracy_score: float | None = None
    hallucination_rate: float | None = None
    faithfulness_score: float | None = None
    retrieval_score: float | None = None
    security_score: float | None = None
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    total_cost_usd: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @property
    def progress_percent(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round((self.completed_questions / self.total_questions) * 100, 1)


class MetricResponse(BaseModel):
    id: uuid.UUID
    evaluator_type: str
    score: float
    explanation: str | None = None
    details: dict | None = None

    model_config = {"from_attributes": True}


class EvaluationResultResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    question_text: str | None = None
    expected_answer: str | None = None
    response_text: str | None = None
    status: str
    overall_score: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    metrics: list[MetricResponse] = []

    model_config = {"from_attributes": True}
