"""Metrics API Endpoints — aggregated analytics."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.evaluation import Evaluation
from app.models.metric import Metric

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/dashboard")
async def dashboard_metrics(
    db: DbSession,
    current_user: CurrentUser,
    project_id: uuid.UUID | None = None,
) -> dict:
    """Get dashboard KPI metrics."""
    base_filter = [Evaluation.org_id == current_user.org_id, Evaluation.status == "completed"]
    if project_id:
        base_filter.append(Evaluation.project_id == project_id)

    stmt = select(
        func.count(Evaluation.id).label("total_evaluations"),
        func.avg(Evaluation.overall_score).label("avg_score"),
        func.avg(Evaluation.accuracy_score).label("avg_accuracy"),
        func.avg(Evaluation.hallucination_rate).label("avg_hallucination_rate"),
        func.avg(Evaluation.faithfulness_score).label("avg_faithfulness"),
        func.avg(Evaluation.retrieval_score).label("avg_retrieval"),
        func.avg(Evaluation.security_score).label("avg_security"),
        func.avg(Evaluation.latency_p50_ms).label("avg_latency_p50"),
        func.avg(Evaluation.latency_p95_ms).label("avg_latency_p95"),
        func.sum(Evaluation.total_cost_usd).label("total_cost"),
    ).where(*base_filter)

    result = await db.execute(stmt)
    row = result.one()

    return {
        "total_evaluations": row.total_evaluations or 0,
        "avg_overall_score": round(float(row.avg_score or 0), 2),
        "avg_accuracy": round(float(row.avg_accuracy or 0), 2),
        "avg_hallucination_rate": round(float(row.avg_hallucination_rate or 0), 2),
        "avg_faithfulness": round(float(row.avg_faithfulness or 0), 2),
        "avg_retrieval_quality": round(float(row.avg_retrieval or 0), 2),
        "avg_security_score": round(float(row.avg_security or 0), 2),
        "avg_latency_p50_ms": round(float(row.avg_latency_p50 or 0), 2),
        "avg_latency_p95_ms": round(float(row.avg_latency_p95 or 0), 2),
        "total_cost_usd": round(float(row.total_cost or 0), 4),
    }


@router.get("/trends")
async def metric_trends(
    db: DbSession,
    current_user: CurrentUser,
    project_id: uuid.UUID | None = None,
    days: int = 30,
) -> list[dict]:
    """Get metric trends over time."""
    from sqlalchemy import cast, Date

    base_filter = [Evaluation.org_id == current_user.org_id, Evaluation.status == "completed"]
    if project_id:
        base_filter.append(Evaluation.project_id == project_id)

    stmt = (
        select(
            cast(Evaluation.completed_at, Date).label("date"),
            func.avg(Evaluation.overall_score).label("avg_score"),
            func.count(Evaluation.id).label("count"),
        )
        .where(*base_filter)
        .group_by(cast(Evaluation.completed_at, Date))
        .order_by(cast(Evaluation.completed_at, Date).desc())
        .limit(days)
    )

    result = await db.execute(stmt)
    return [
        {
            "date": row.date.isoformat() if row.date else None,
            "avg_score": round(float(row.avg_score or 0), 2),
            "evaluation_count": row.count,
        }
        for row in result.all()
    ]
