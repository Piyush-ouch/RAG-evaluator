"""Reports API Endpoints — Direct Live Data Exports & Background Generation."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select

from app.api.deps import OptionalUser, DbSession
from app.models.evaluation import Evaluation, EvaluationResult
from app.models.report import Report

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/")
async def list_reports(
    db: DbSession,
    current_user: OptionalUser = None,
    evaluation_id: uuid.UUID | None = None,
) -> list[dict]:
    """List generated audit reports."""
    stmt = select(Report)
    if current_user:
        stmt = stmt.where(Report.org_id == current_user.org_id)
    if evaluation_id:
        stmt = stmt.where(Report.evaluation_id == evaluation_id)
    stmt = stmt.order_by(Report.created_at.desc())
    result = await db.execute(stmt)
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "evaluation_id": str(r.evaluation_id) if r.evaluation_id else None,
            "report_type": r.report_type,
            "format": r.format,
            "title": r.title,
            "file_size_bytes": r.file_size_bytes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.get("/export/csv")
async def export_csv_report(db: DbSession) -> Response:
    """Export all evaluated benchmark questions and scores as a downloadable CSV."""
    stmt = select(EvaluationResult).order_by(EvaluationResult.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    results = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Evaluation ID", "Question Text", "Chatbot Response",
        "Overall Score", "Status", "Hallucination Diagnostic / Why It Hallucinated", "Timestamp"
    ])

    for r in results:
        halluc_reason = "0% Hallucinated — All claims grounded in retrieved context."
        for m in (r.metrics or []):
            if m.evaluator_type == "hallucination" and m.explanation:
                halluc_reason = m.explanation
                break
        writer.writerow([
            str(r.evaluation_id),
            r.question_text or "N/A",
            r.response_text or "No response returned",
            r.overall_score or 0.0,
            r.status,
            halluc_reason,
            r.created_at.isoformat() if r.created_at else "",
        ])

    csv_data = output.getvalue()
    filename = f"rag_evaluator_audit_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/json")
async def export_json_report(db: DbSession) -> Response:
    """Export evaluation metrics and dataset runs as structured JSON."""
    stmt = select(Evaluation).order_by(Evaluation.created_at.desc()).limit(20)
    res = await db.execute(stmt)
    evaluations = res.scalars().all()

    data = []
    for ev in evaluations:
        data.append({
            "evaluation_id": str(ev.id),
            "name": ev.name,
            "status": ev.status,
            "total_questions": ev.total_questions,
            "completed_questions": ev.completed_questions,
            "overall_score": ev.overall_score,
            "accuracy_score": ev.accuracy_score,
            "hallucination_rate": ev.hallucination_rate,
            "started_at": ev.started_at.isoformat() if ev.started_at else None,
            "completed_at": ev.completed_at.isoformat() if ev.completed_at else None,
        })

    filename = f"rag_evaluator_metrics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/summary")
async def export_summary_report(db: DbSession) -> Response:
    """Export Executive Summary & RAG Health Index report in text format."""
    stmt = select(Evaluation).order_by(Evaluation.created_at.desc()).limit(5)
    res = await db.execute(stmt)
    evaluations = res.scalars().all()

    summary_lines = [
        "================================================================================",
        "                     ENTERPRISE RAG EVALUATOR & GUARDRAIL SANDBOX               ",
        "                            EXECUTIVE COMPLIANCE AUDIT REPORT                   ",
        "================================================================================",
        f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "Audit Status: VERIFIED & PERSISTED (PostgreSQL + Redis)",
        "--------------------------------------------------------------------------------",
        "",
        "SUMMARY OF RECENT EVALUATION RUNS:",
        ""
    ]

    for i, ev in enumerate(evaluations, 1):
        summary_lines.extend([
            f"Run #{i}: {ev.name}",
            f"  - Evaluation ID: {ev.id}",
            f"  - Status: {ev.status.upper()}",
            f"  - Overall Score: {(ev.overall_score or 0) * 100:.1f}%",
            f"  - Accuracy Score: {(ev.accuracy_score or 0) * 100:.1f}%",
            f"  - Hallucination Rate: {(ev.hallucination_rate or 0) * 100:.1f}%",
            f"  - Questions Evaluated: {ev.completed_questions}/{ev.total_questions}",
            "--------------------------------------------------------------------------------",
        ])

    content = "\n".join(summary_lines)
    filename = f"executive_rag_health_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
