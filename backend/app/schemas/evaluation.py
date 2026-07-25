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
    difficulty: str
    order_index: int
    tags: list = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


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


class EvaluationResultResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    response_text: str | None = None
    status: str
    overall_score: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    model_config = {"from_attributes": True}


class MetricResponse(BaseModel):
    id: uuid.UUID
    evaluator_type: str
    score: float
    explanation: str | None = None

    model_config = {"from_attributes": True}
