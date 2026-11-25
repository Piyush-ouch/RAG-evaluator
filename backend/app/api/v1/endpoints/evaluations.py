"""
Evaluation API Endpoints
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, OptionalUser, Pagination, require_role
from app.core.constants import UserRole
from app.models.evaluation import Evaluation, EvaluationResult
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationResultResponse,
)
from app.services.benchmark_service import BenchmarkService
from app.services.evaluation_service import EvaluationService
from app.services.project_service import ProjectService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


class QuickStartEvaluationRequest(BaseModel):
    chatbot_url: str = Field(..., description="Target Chatbot API Endpoint URL")
    suite_id: uuid.UUID | None = None
    questions: list[str] | None = None
    enabled_evaluators: list[str] | None = None


class QuickStartEvaluationResponse(BaseModel):
    evaluation_id: str
    status: str
    total_questions: int
    message: str


@router.post("/quick-start", response_model=QuickStartEvaluationResponse, status_code=202)
async def quick_start_evaluation(
    request: QuickStartEvaluationRequest,
    db: DbSession,
    current_user: OptionalUser,
) -> QuickStartEvaluationResponse:
    """
    Quick-start evaluation execution.

    Allows launching an evaluation immediately against a target chatbot API URL
    without requiring manual project setup. Automatically seeds or resolves a project
    and benchmark suite.
    """
    project_svc = ProjectService(db)
    benchmark_svc = BenchmarkService(db)
    eval_svc = EvaluationService(db)

    # Resolve organization ID
    if current_user:
        default_org_id = current_user.org_id
    else:
        from app.models.organization import Organization
        org_stmt = select(Organization).limit(1)
        org_res = await db.execute(org_stmt)
        existing_org = org_res.scalar_one_or_none()
        if existing_org:
            default_org_id = existing_org.id
        else:
            new_org = Organization(
                name="Default Organization",
                slug="default-org",
            )
            db.add(new_org)
            await db.flush()
            default_org_id = new_org.id

    # Find or create quick-start project
    projects = await project_svc.list_projects(default_org_id)

    target_project = None
    for p in projects:
        if p.chatbot_api_url == request.chatbot_url:
            target_project = p
            break

    if not target_project:
        target_project = await project_svc.create_project(
            org_id=default_org_id,
            name="Default Chatbot Project",
            description="Auto-created project for quick-start evaluations",
            chatbot_api_url=request.chatbot_url,
        )

    # Resolve benchmark suite
    target_suite = None
    if request.suite_id:
        target_suite = await benchmark_svc.get_suite(request.suite_id)

    if not target_suite:
        suites = await benchmark_svc.seed_default_suites(target_project.id, default_org_id)
        target_suite = suites[0]

    evaluation = await eval_svc.create_evaluation_run(
        org_id=default_org_id,
        project_id=target_project.id,
        suite_id=target_suite.id,
        name=f"Evaluation Run — {target_suite.name}",
        enabled_evaluators=request.enabled_evaluators,
        triggered_by_id=current_user.id if current_user else None,
    )

    return QuickStartEvaluationResponse(
        evaluation_id=str(evaluation.id),
        status=evaluation.status,
        total_questions=evaluation.total_questions,
        message="Evaluation run queued successfully in PostgreSQL and Redis.",
    )


@router.get("/", response_model=list[EvaluationResponse])
async def list_evaluations(
    db: DbSession,
    current_user: OptionalUser,
    project_id: uuid.UUID | None = None,
) -> list[EvaluationResponse]:
    """List evaluations for the organization (supports unauthenticated demo mode)."""
    svc = EvaluationService(db)
    if current_user:
        org_id = current_user.org_id
    else:
        from app.models.organization import Organization
        org_stmt = select(Organization).limit(1)
        org_res = await db.execute(org_stmt)
        existing_org = org_res.scalar_one_or_none()
        if existing_org:
            org_id = existing_org.id
        else:
            return []

    evaluations = await svc.list_evaluations(org_id, project_id)
    return [EvaluationResponse.model_validate(e, from_attributes=True) for e in evaluations]


@router.post(
    "/",
    response_model=EvaluationResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def create_evaluation(
    request: EvaluationCreate,
    project_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> EvaluationResponse:
    """Create and start a new evaluation."""
    svc = EvaluationService(db)
    evaluation = await svc.create_evaluation_run(
        org_id=current_user.org_id,
        project_id=project_id,
        suite_id=request.suite_id,
        name=request.name,
        enabled_evaluators=request.enabled_evaluators,
        triggered_by_id=current_user.id,
        version_tag=request.version_tag,
    )
    return EvaluationResponse.model_validate(evaluation, from_attributes=True)


@router.get("/{eval_id}", response_model=EvaluationResponse)
async def get_evaluation(
    eval_id: uuid.UUID,
    db: DbSession,
    current_user: OptionalUser,
) -> EvaluationResponse:
    """Get evaluation details."""
    svc = EvaluationService(db)
    org_id = current_user.org_id if current_user else None
    evaluation = await svc.get_evaluation(eval_id, org_id)
    return EvaluationResponse.model_validate(evaluation, from_attributes=True)


@router.get("/{eval_id}/results", response_model=list[EvaluationResultResponse])
async def get_evaluation_results(
    eval_id: uuid.UUID,
    db: DbSession,
    pagination: Pagination,
) -> list[EvaluationResultResponse]:
    """Get paginated evaluation results."""
    svc = EvaluationService(db)
    results = await svc.get_results(eval_id, pagination.page, pagination.page_size)
    return [EvaluationResultResponse.model_validate(r, from_attributes=True) for r in results]


@router.post("/{eval_id}/cancel")
async def cancel_evaluation(
    eval_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Cancel a running evaluation."""
    svc = EvaluationService(db)
    await svc.cancel_evaluation(eval_id, current_user.org_id)
    return {"message": "Evaluation cancelled successfully."}
