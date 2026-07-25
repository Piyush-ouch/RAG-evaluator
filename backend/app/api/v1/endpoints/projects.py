"""
Project API Endpoints
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends
from slugify import slugify
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.core.security import encrypt_value
from app.models.llm_provider import LLMProviderConfig
from app.models.project import Project
from app.models.vector_db import VectorDBConfig
from app.schemas.project import (
    ChatbotConfigRequest,
    ConnectionTestResponse,
    LLMConfigRequest,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    VectorDBConfigRequest,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
) -> list[ProjectResponse]:
    """List projects in the current organization."""
    stmt = (
        select(Project)
        .where(
            Project.org_id == current_user.org_id,
            Project.deleted_at.is_(None),
        )
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p, from_attributes=True) for p in projects]


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def create_project(
    request: ProjectCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ProjectResponse:
    """Create a new project."""
    project = Project(
        name=request.name,
        slug=slugify(request.name),
        description=request.description,
        chatbot_api_url=request.chatbot_api_url,
        chatbot_api_method=request.chatbot_api_method,
        org_id=current_user.org_id,
        created_by_id=current_user.id,
        settings={},
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    logger.info("project_created", project_id=str(project.id))
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ProjectResponse:
    """Get project details."""
    stmt = select(Project).where(
        Project.id == uuid.UUID(project_id),
        Project.org_id == current_user.org_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", project_id)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ProjectResponse:
    """Update project details."""
    stmt = select(Project).where(
        Project.id == uuid.UUID(project_id),
        Project.org_id == current_user.org_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", project_id)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    return ProjectResponse.model_validate(project, from_attributes=True)


@router.post(
    "/{project_id}/configure-llm",
    status_code=201,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def configure_llm(
    project_id: str,
    request: LLMConfigRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Configure an LLM provider for a project."""
    config = LLMProviderConfig(
        project_id=uuid.UUID(project_id),
        org_id=current_user.org_id,
        name=request.name,
        provider_type=request.provider_type,
        model_name=request.model_name,
        api_key_encrypted=encrypt_value(request.api_key) if request.api_key else None,
        api_base_url=request.api_base_url,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        is_judge=request.is_judge,
    )
    db.add(config)
    await db.flush()
    return {"message": "LLM provider configured.", "id": str(config.id)}


@router.post(
    "/{project_id}/configure-vectordb",
    status_code=201,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def configure_vectordb(
    project_id: str,
    request: VectorDBConfigRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Configure a vector database for a project."""
    config = VectorDBConfig(
        project_id=uuid.UUID(project_id),
        org_id=current_user.org_id,
        name=request.name,
        provider_type=request.provider_type,
        connection_config=request.connection_config,
        api_key_encrypted=encrypt_value(request.api_key) if request.api_key else None,
        collection_name=request.collection_name,
        embedding_model=request.embedding_model,
        embedding_dimensions=request.embedding_dimensions,
    )
    db.add(config)
    await db.flush()
    return {"message": "Vector database configured.", "id": str(config.id)}


@router.post("/{project_id}/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    project_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ConnectionTestResponse:
    """Test connectivity to the project's chatbot API."""
    import time
    import httpx

    stmt = select(Project).where(
        Project.id == uuid.UUID(project_id),
        Project.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project or not project.chatbot_api_url:
        return ConnectionTestResponse(
            success=False, message="No chatbot API URL configured."
        )

    try:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method="GET",
                url=project.chatbot_api_url,
            )
        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResponse(
            success=resp.status_code < 500,
            message=f"Status: {resp.status_code}",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False, message=f"Connection failed: {str(e)}"
        )
