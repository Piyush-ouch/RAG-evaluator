"""
Base Evaluator & Evaluation Context

Defines the contract for all evaluators and the context they receive.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationContext:
    """
    All data needed by evaluators for a single question.

    This is the input contract — evaluators receive a fully
    populated context and return an EvaluationScore.
    """
    question_text: str
    expected_answer: str | None = None
    response_text: str | None = None
    retrieved_chunks: list[str] = field(default_factory=list)
    chunk_sources: list[str] = field(default_factory=list)
    chunk_scores: list[float] = field(default_factory=list)
    expected_context: list[str] = field(default_factory=list)
    expected_citations: list[str] = field(default_factory=list)
    response_citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    provider: str = ""
    model_name: str = ""


@dataclass
class EvaluationScore:
    """
    Output of an evaluator.

    score: Normalized 0.0-1.0 (1.0 = perfect)
    passed: Binary pass/fail for threshold-based evaluators
    explanation: Human-readable reasoning
    details: Structured data for drill-down
    """
    evaluator_type: str
    score: float
    passed: bool = True
    explanation: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.

    Every evaluator must implement:
    - name: Unique identifier
    - description: What it measures
    - evaluate(): The scoring logic
    """

    name: str
    description: str
    version: str = "1.0"

    @abstractmethod
    async def evaluate(self, context: EvaluationContext) -> EvaluationScore:
        """
        Evaluate the response against the context.

        Must return an EvaluationScore with:
        - score: 0.0 to 1.0
        - explanation: Why this score was given
        - details: Any supporting data
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
