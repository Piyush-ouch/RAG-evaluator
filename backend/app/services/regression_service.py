"""
Regression Service & Quality Gate Engine

Computes metric deltas between baseline and candidate evaluation runs.
Enforces automatic Quality Gates for CI/CD deployment blocking.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.regression import RegressionHistory


class QualityGateConfig:
    """Threshold limits for CI/CD Quality Gates."""
    def __init__(
        self,
        max_allowed_hallucination_increase: float = 0.05,
        max_allowed_accuracy_drop: float = 0.05,
        max_allowed_security_drop: float = 0.05,
        max_allowed_latency_increase_ms: float = 1000.0,
    ):
        self.max_allowed_hallucination_increase = max_allowed_hallucination_increase
        self.max_allowed_accuracy_drop = max_allowed_accuracy_drop
        self.max_allowed_security_drop = max_allowed_security_drop
        self.max_allowed_latency_increase_ms = max_allowed_latency_increase_ms


class RegressionService:
    """Service layer for evaluating quality regression between release runs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare_evaluations(
        self,
        project_id: uuid.UUID,
        baseline_id: uuid.UUID,
        candidate_id: uuid.UUID,
        gate_config: QualityGateConfig | None = None,
    ) -> RegressionHistory:
        """Compare two evaluation runs and record regression metrics."""
        gate_config = gate_config or QualityGateConfig()

        stmt = select(Evaluation).where(Evaluation.id.in_([baseline_id, candidate_id]))
        result = await self.db.execute(stmt)
        evals = {e.id: e for e in result.scalars().all()}

        baseline = evals.get(baseline_id)
        candidate = evals.get(candidate_id)

        if not baseline or not candidate:
            raise ValueError("Baseline or Candidate evaluation not found.")

        # Compute metric deltas
        overall_delta = (candidate.overall_score or 0.0) - (baseline.overall_score or 0.0)
        accuracy_delta = (candidate.accuracy_score or 0.0) - (baseline.accuracy_score or 0.0)
        hallucination_delta = (candidate.hallucination_rate or 0.0) - (baseline.hallucination_rate or 0.0)
        faithfulness_delta = (candidate.faithfulness_score or 0.0) - (baseline.faithfulness_score or 0.0)
        security_delta = (candidate.security_score or 0.0) - (baseline.security_score or 0.0)

        # Quality Gate Check
        has_regression = False
        reasons = []

        if hallucination_delta > gate_config.max_allowed_hallucination_increase:
            has_regression = True
            reasons.append(f"Hallucination rate increased by +{round(hallucination_delta*100, 1)}% (threshold: {gate_config.max_allowed_hallucination_increase*100}%)")

        if accuracy_delta < -gate_config.max_allowed_accuracy_drop:
            has_regression = True
            reasons.append(f"Accuracy score dropped by {round(accuracy_delta*100, 1)}% (threshold: {gate_config.max_allowed_accuracy_drop*100}%)")

        if security_delta < -gate_config.max_allowed_security_drop:
            has_regression = True
            reasons.append(f"Security score dropped by {round(security_delta*100, 1)}% (threshold: {gate_config.max_allowed_security_drop*100}%)")

        summary_text = "PASSED: No regression detected." if not has_regression else f"FAILED: {'; '.join(reasons)}"

        history = RegressionHistory(
            project_id=project_id,
            org_id=baseline.org_id,
            eval_baseline_id=baseline_id,
            eval_candidate_id=candidate_id,
            overall_delta=round(overall_delta, 3),
            accuracy_delta=round(accuracy_delta, 3),
            hallucination_delta=round(hallucination_delta, 3),
            faithfulness_delta=round(faithfulness_delta, 3),
            security_delta=round(security_delta, 3),
            summary=summary_text,
            has_regression=has_regression,
        )

        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history
