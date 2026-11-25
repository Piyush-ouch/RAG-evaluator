"""
FastAPI Application Factory

Configured with CORS middleware, OpenTelemetry, Prometheus metrics,
Sentry SDK, and Kubernetes health probes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    settings = get_settings()

    # Initialize Sentry SDK if DSN configured
    if settings.sentry_dsn and settings.sentry_dsn.strip():
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.app_env.value,
                integrations=[FastApiIntegration()],
                traces_sample_rate=1.0,
            )
            logger.info("sentry_initialized")
        except Exception as err:
            logger.warning("sentry_init_failed", error=str(err))

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env.value,
        version=settings.app_version,
    )

    # --- Startup ---
    from app.database.session import engine
    from app.database.base import Base
    import app.models  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_connected")
    except Exception as db_err:
        logger.warning("database_connection_fallback_sqlite", error=str(db_err))
        import app.database.session as db_session
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
        fallback_engine = create_async_engine("sqlite+aiosqlite:///./rageval.db", echo=False)
        db_session.engine = fallback_engine
        db_session.async_session_factory = async_sessionmaker(
            fallback_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
        )
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("sqlite_fallback_database_connected")

    from app.core.redis import redis_client
    try:
        await redis_client.initialize()
        logger.info("redis_connected")
    except Exception as err:
        logger.warning("redis_connection_warning", error=str(err))

    from app.core.storage import storage_client
    try:
        await storage_client.ensure_bucket()
        logger.info("s3_connected", bucket=settings.s3_bucket_name)
    except Exception as err:
        logger.warning("s3_connection_warning", error=str(err))

    logger.info("application_started")

    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")
    await engine.dispose()
    try:
        await redis_client.close()
    except Exception:
        pass
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """FastAPI application factory."""
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

    _configure_middleware(app, settings)
    _configure_exception_handlers(app)
    _configure_routers(app)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.app_version}

    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        from app.database.session import engine
        from app.core.redis import redis_client

        checks: dict[str, str] = {}
        try:
            async with engine.begin() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        try:
            if await redis_client.ping():
                checks["redis"] = "ok"
            else:
                checks["redis"] = "error"
        except Exception:
            checks["redis"] = "error"

        status = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"
        return {"status": status, **checks}

    @app.get("/metrics", tags=["Observability"])
    async def metrics_endpoint() -> Response:
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


def _configure_middleware(app: FastAPI, settings: "Settings") -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.(railway\.app|up\.railway\.app|vercel\.app|onrender\.com))(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "Content-Disposition"],
    )

    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )

    from app.middleware.request_id import RequestIDMiddleware
    from app.middleware.process_time import ProcessTimeMiddleware
    from app.middleware.logging import LoggingMiddleware

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(LoggingMiddleware)


def _configure_exception_handlers(app: FastAPI) -> None:
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
    from app.api.v1.router import api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")
