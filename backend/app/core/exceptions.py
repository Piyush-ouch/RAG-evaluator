"""
Custom Exception Hierarchy & FastAPI Exception Handlers

Structured exception classes that map to HTTP responses.
Each exception carries a machine-readable error code for
frontend consumption and a human-readable detail message.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------
# Base Exception
# ---------------------------------------------------------

class AppException(Exception):
    """
    Base exception for all application errors.

    Attributes:
        status_code: HTTP status code.
        error_code: Machine-readable error identifier (e.g., "AUTH_TOKEN_EXPIRED").
        detail: Human-readable error message.
        headers: Optional HTTP headers to include in the response.
    """

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        detail: str = "An unexpected error occurred.",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.headers = headers
        super().__init__(self.detail)


# ---------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------

class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Could not validate credentials.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_INVALID_CREDENTIALS",
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(AppException):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_TOKEN_EXPIRED",
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsError(AppException):
    """Raised when a user lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH_INSUFFICIENT_PERMISSIONS",
            detail=detail,
        )


# ---------------------------------------------------------
# Resource Errors
# ---------------------------------------------------------

class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: Any = None) -> None:
        detail = f"{resource} not found."
        if identifier:
            detail = f"{resource} with id '{identifier}' not found."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            detail=detail,
        )


class ConflictError(AppException):
    """Raised when a resource already exists or conflicts with current state."""

    def __init__(self, detail: str = "Resource already exists.") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            detail=detail,
        )


class ValidationError(AppException):
    """Raised for business-logic validation failures (not schema validation)."""

    def __init__(self, detail: str = "Validation failed.") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            detail=detail,
        )


# ---------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------

class RateLimitExceededError(AppException):
    """Raised when a client exceeds their rate limit."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


# ---------------------------------------------------------
# External Service Errors
# ---------------------------------------------------------

class ExternalServiceError(AppException):
    """Raised when an external service (LLM, VectorDB, etc.) fails."""

    def __init__(self, service: str, detail: str = "Service unavailable.") -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            detail=f"{service}: {detail}",
        )


class ProviderConfigurationError(AppException):
    """Raised when a provider is misconfigured."""

    def __init__(self, provider: str, detail: str = "Provider not configured.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PROVIDER_CONFIG_ERROR",
            detail=f"{provider}: {detail}",
        )


# ---------------------------------------------------------
# Billing
# ---------------------------------------------------------

class BillingError(AppException):
    """Raised for billing-related errors."""

    def __init__(self, detail: str = "Billing error.") -> None:
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="BILLING_ERROR",
            detail=detail,
        )


class QuotaExceededError(AppException):
    """Raised when an organization exceeds their usage quota."""

    def __init__(self, detail: str = "Usage quota exceeded. Please upgrade your plan.") -> None:
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="QUOTA_EXCEEDED",
            detail=detail,
        )


# ---------------------------------------------------------
# Exception Handlers (registered in main.py)
# ---------------------------------------------------------

async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
    """Handler for all AppException subclasses."""
    logger.warning(
        "app_exception",
        error_code=exc.error_code,
        detail=exc.detail,
        status_code=exc.status_code,
        path=str(request.url),
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    """Handler for Pydantic/FastAPI validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "validation_error",
        errors=errors,
        path=str(request.url),
    )
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": errors,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    In production, this hides implementation details.
    In development, it includes the traceback.
    """
    logger.exception(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        detail=str(exc),
        path=str(request.url),
    )

    from app.config import get_settings
    settings = get_settings()

    detail = str(exc) if settings.is_development else "An internal error occurred."

    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": detail,
            }
        },
    )
