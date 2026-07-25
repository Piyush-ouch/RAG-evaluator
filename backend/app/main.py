"""
FastAPI Application Factory

Uses the factory pattern to create the FastAPI application instance.
This allows different configurations for testing, development, and production.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database pool, Redis connection, S3 client
    - Shutdown: Close all connections gracefully
    """
    settings = get_settings()
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env.value,
        version=settings.app_version,
    )

    # --- Startup ---
    from app.database.session import engine

    # Verify database connectivity
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
    logger.info("database_connected")

    # Initialize Redis
    from app.core.redis import redis_client
    await redis_client.initialize()
    logger.info("redis_connected")

    # Initialize S3
    from app.core.storage import storage_client
    await storage_client.ensure_bucket()
    logger.info("s3_connected", bucket=settings.s3_bucket_name)

    logger.info("application_started")

    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")

    from app.database.session import engine
    await engine.dispose()

    from app.core.redis import redis_client
    await redis_client.close()

    logger.info("application_stopped")


def create_app() -> FastAPI:
    """
    FastAPI application factory.

    Creates and configures the FastAPI application with:
    - CORS middleware
    - Trusted host middleware
    - Exception handlers
    - API routers
    - OpenAPI documentation
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Enterprise RAG Sandbox & Guardrail Evaluator — "
            "Test, evaluate, monitor, and benchmark RAG systems "
            "with comprehensive AI quality and security metrics."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else "/api/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ---------------------------------------------------------
    # Middleware (order matters — outermost first)
    # ---------------------------------------------------------
    _configure_middleware(app, settings)

    # ---------------------------------------------------------
    # Exception Handlers
    # ---------------------------------------------------------
    _configure_exception_handlers(app)

    # ---------------------------------------------------------
    # Routers
    # ---------------------------------------------------------
    _configure_routers(app)

    # ---------------------------------------------------------
    # Health Check
    # ---------------------------------------------------------
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.app_version}

    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        """Kubernetes readiness probe — checks all dependencies."""
        from app.database.session import engine
        from app.core.redis import redis_client

        checks: dict[str, str] = {}

        # Database
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        # Redis
        try:
            if await redis_client.ping():
                checks["redis"] = "ok"
            else:
                checks["redis"] = "error"
        except Exception:
            checks["redis"] = "error"

        status = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"
        return {"status": status, **checks}

    return app


def _configure_middleware(app: FastAPI, settings: "Settings") -> None:  # noqa: F821
    """Configure application middleware stack."""
    from app.config import Settings  # noqa: F811

    # CORS — allow configured origins + any localhost port in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins],
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?" if settings.is_development else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # Trusted Hosts (production only)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )

    # Custom middleware
    from app.middleware.request_id import RequestIDMiddleware
    from app.middleware.process_time import ProcessTimeMiddleware
    from app.middleware.logging import LoggingMiddleware

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(LoggingMiddleware)


def _configure_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""
    from app.core.exceptions import (
        AppException,
        app_exception_handler,
        unhandled_exception_handler,
        validation_exception_handler,
    )
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _configure_routers(app: FastAPI) -> None:
    """Mount all API routers."""
    from app.api.v1.router import api_v1_router

    app.include_router(api_v1_router, prefix="/api/v1")
