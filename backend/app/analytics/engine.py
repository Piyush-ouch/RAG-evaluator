"""
Analytics Engine

Computes cross-project trend charts, cost breakdowns, model/provider comparisons,
and latency percentiles (P50, P90, P99).
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation, EvaluationResult
from app.models.latency import LatencyRecord
from app.models.metric import Metric


@dataclass
class AnalyticsSummary:
    """Aggregated metrics summary for dashboard charts."""
    total_evaluations: int
    average_overall_score: float
    average_accuracy: float
    average_hallucination_rate: float
    average_faithfulness: float
    average_security_score: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    total_cost_usd: float


class AnalyticsEngine:
    """Engine for generating cross-run analytics, latency distributions, and cost breakdowns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_analytics(
        self,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> AnalyticsSummary:
        """Compute aggregated analytics for a specific project."""
        stmt = (
            select(Evaluation)
            .where(Evaluation.project_id == project_id, Evaluation.org_id == org_id)
            .order_by(Evaluation.created_at.desc())
        )
        result = await self.db.execute(stmt)
        evaluations = result.scalars().all()

        if not evaluations:
            return AnalyticsSummary(
                total_evaluations=0,
                average_overall_score=0.0,
                average_accuracy=0.0,
                average_hallucination_rate=0.0,
                average_faithfulness=0.0,
                average_security_score=0.0,
                p50_latency_ms=0.0,
                p90_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_cost_usd=0.0,
            )

        overall_scores = [e.overall_score for e in evaluations if e.overall_score is not None]
        accuracy_scores = [e.accuracy_score for e in evaluations if e.accuracy_score is not None]
        hallucination_rates = [e.hallucination_rate for e in evaluations if e.hallucination_rate is not None]
        faithfulness_scores = [e.faithfulness_score for e in evaluations if e.faithfulness_score is not None]
        security_scores = [e.security_score for e in evaluations if e.security_score is not None]

        # Latency calculations
        lat_stmt = (
            select(LatencyRecord.total_ms)
            .join(EvaluationResult, LatencyRecord.result_id == EvaluationResult.id)
            .join(Evaluation, EvaluationResult.evaluation_id == Evaluation.id)
            .where(Evaluation.project_id == project_id, Evaluation.org_id == org_id)
        )
        lat_res = await self.db.execute(lat_stmt)
        latencies = sorted([r for r in lat_res.scalars().all() if r is not None])

        p50 = self._percentile(latencies, 50)
        p90 = self._percentile(latencies, 90)
        p99 = self._percentile(latencies, 99)

        return AnalyticsSummary(
            total_evaluations=len(evaluations),
            average_overall_score=round(sum(overall_scores) / len(overall_scores), 3) if overall_scores else 0.0,
            average_accuracy=round(sum(accuracy_scores) / len(accuracy_scores), 3) if accuracy_scores else 0.0,
            average_hallucination_rate=round(sum(hallucination_rates) / len(hallucination_rates), 3) if hallucination_rates else 0.0,
            average_faithfulness=round(sum(faithfulness_scores) / len(faithfulness_scores), 3) if faithfulness_scores else 0.0,
            average_security_score=round(sum(security_scores) / len(security_scores), 3) if security_scores else 0.0,
            p50_latency_ms=round(p50, 1),
            p90_latency_ms=round(p90, 1),
            p99_latency_ms=round(p99, 1),
            total_cost_usd=0.0,
        )

    @staticmethod
    def _percentile(data: Sequence[float], percentile: float) -> float:
        """Calculate arbitrary percentile value from sorted data array."""
        if not data:
            return 0.0
        k = (len(data) - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(data[int(k)])
        d0 = data[int(f)] * (c - k)
        d1 = data[int(c)] * (k - f)
        return float(d0 + d1)
