"""
Benchmark API Endpoints
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.models.benchmark import BenchmarkSuite, Question
from app.schemas.evaluation import (
    BenchmarkSuiteCreate,
    BenchmarkSuiteResponse,
    QuestionCreate,
    QuestionResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.get("/", response_model=list[BenchmarkSuiteResponse])
async def list_benchmark_suites(
    db: DbSession,
    current_user: CurrentUser,
    project_id: uuid.UUID | None = None,
) -> list[BenchmarkSuiteResponse]:
    """List benchmark suites."""
    stmt = select(BenchmarkSuite).where(
        BenchmarkSuite.org_id == current_user.org_id,
    )
    if project_id:
        stmt = stmt.where(BenchmarkSuite.project_id == project_id)
    stmt = stmt.order_by(BenchmarkSuite.created_at.desc())
    result = await db.execute(stmt)
    suites = result.scalars().all()
    return [BenchmarkSuiteResponse.model_validate(s, from_attributes=True) for s in suites]


@router.post("/", response_model=BenchmarkSuiteResponse, status_code=201)
async def create_benchmark_suite(
    request: BenchmarkSuiteCreate,
    project_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BenchmarkSuiteResponse:
    """Create a new benchmark suite."""
    suite = BenchmarkSuite(
        project_id=project_id,
        org_id=current_user.org_id,
        name=request.name,
        description=request.description,
        domain=request.domain,
    )
    db.add(suite)
    await db.flush()
    await db.refresh(suite)
    return BenchmarkSuiteResponse.model_validate(suite, from_attributes=True)


@router.get("/{suite_id}", response_model=BenchmarkSuiteResponse)
async def get_benchmark_suite(
    suite_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BenchmarkSuiteResponse:
    """Get benchmark suite details."""
    stmt = select(BenchmarkSuite).where(
        BenchmarkSuite.id == suite_id,
        BenchmarkSuite.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()
    if not suite:
        raise NotFoundError("BenchmarkSuite", str(suite_id))
    return BenchmarkSuiteResponse.model_validate(suite, from_attributes=True)


@router.post("/{suite_id}/questions", response_model=list[QuestionResponse], status_code=201)
async def add_questions(
    suite_id: uuid.UUID,
    questions: list[QuestionCreate],
    db: DbSession,
    current_user: CurrentUser,
) -> list[QuestionResponse]:
    """Add questions to a benchmark suite."""
    stmt = select(BenchmarkSuite).where(
        BenchmarkSuite.id == suite_id,
        BenchmarkSuite.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    suite = result.scalar_one_or_none()
    if not suite:
        raise NotFoundError("BenchmarkSuite", str(suite_id))

    created = []
    for i, q in enumerate(questions):
        question = Question(
            suite_id=suite_id,
            text=q.text,
            expected_answer=q.expected_answer,
            category=q.category,
            difficulty=q.difficulty,
            tags=q.tags,
            expected_context=q.expected_context,
            expected_citations=q.expected_citations,
            order_index=suite.question_count + i,
        )
        db.add(question)
        created.append(question)

    suite.question_count += len(questions)
    await db.flush()
    for q in created:
        await db.refresh(q)
    return [QuestionResponse.model_validate(q, from_attributes=True) for q in created]


@router.post("/{suite_id}/import", status_code=201)
async def import_dataset(
    suite_id: uuid.UUID,
    file: UploadFile = File(...),
    db: DbSession = None,
    current_user: CurrentUser = None,
) -> dict:
    """Import questions from CSV, JSON, or Excel file."""
    if not file.filename:
        raise ValueError("No file provided.")

    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower()

    # Dispatch to background task for large files
    from app.workers.tasks.data_tasks import process_dataset_upload
    task = process_dataset_upload.delay(
        suite_id=str(suite_id),
        file_content=content.decode("utf-8") if ext != "xlsx" else content.hex(),
        file_extension=ext,
        org_id=str(current_user.org_id),
    )

    return {"message": "Dataset import started.", "task_id": task.id}


@router.get("/templates/", response_model=list[BenchmarkSuiteResponse])
async def list_templates(db: DbSession) -> list[BenchmarkSuiteResponse]:
    """List built-in benchmark templates."""
    stmt = select(BenchmarkSuite).where(BenchmarkSuite.is_template == True)  # noqa: E712
    result = await db.execute(stmt)
    return [BenchmarkSuiteResponse.model_validate(s, from_attributes=True)
            for s in result.scalars().all()]
