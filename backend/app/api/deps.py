"""
FastAPI Dependencies — Dependency Injection Layer

Provides reusable dependencies for:
- Database sessions
- Current authenticated user
- Current organization context
- API key authentication
- Pagination parameters
"""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.exceptions import AuthenticationError, InsufficientPermissionsError, TokenExpiredError
from app.core.security import decode_token, verify_api_key
from app.database.session import get_db

logger = structlog.get_logger(__name__)

# HTTP Bearer scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------
# Database Session
# ---------------------------------------------------------
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------
# Pagination
# ---------------------------------------------------------
class PaginationParams:
    """Common pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size


Pagination = Annotated[PaginationParams, Depends()]


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------
async def get_current_user(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """
    Extract and validate the current user from JWT token or API key.

    Priority:
    1. Bearer JWT token (for web/mobile clients)
    2. X-API-Key header (for programmatic access)

    Returns the User ORM instance.
    """
    from app.models.user import User

    if credentials:
        return await _authenticate_jwt(db, credentials.credentials)
    elif x_api_key:
        return await _authenticate_api_key(db, x_api_key)
    else:
        raise AuthenticationError("No authentication credentials provided.")


async def _authenticate_jwt(db: AsyncSession, token: str):
    """Authenticate via JWT token."""
    from app.models.user import User
    from app.core.redis import redis_client

    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthenticationError("Invalid or expired token.")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type. Expected access token.")

    # Check if token is blacklisted (logged out)
    jti = payload.get("jti")
    if jti and await redis_client.is_token_blacklisted(jti):
        raise AuthenticationError("Token has been revoked.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload.")

    from app.database.repositories.base import BaseRepository
    repo = BaseRepository(User, db)
    user = await repo.get_by_id(uuid.UUID(user_id))

    if user is None:
        raise AuthenticationError("User not found.")

    if user.is_deleted:  # type: ignore
        raise AuthenticationError("User account has been deactivated.")

    return user


async def _authenticate_api_key(db: AsyncSession, raw_key: str):
    """Authenticate via API key."""
    from app.models.api_key import ApiKey
    from app.models.user import User
    from sqlalchemy import select

    # Look up API keys (we need to check all since we hash them)
    stmt = select(ApiKey).where(
        ApiKey.is_active == True,  # noqa: E712
        ApiKey.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    api_keys = result.scalars().all()

    for api_key in api_keys:
        if verify_api_key(raw_key, api_key.key_hash):
            # Update last_used
            api_key.last_used_at = __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            )
            await db.flush()

            # Load the associated user (service account or creator)
            user_repo = BaseRepository(User, db)
            user = await user_repo.get_by_id(api_key.created_by_id)
            if user:
                # Attach API key permissions to user context
                user._api_key_permissions = api_key.permissions  # type: ignore
                return user

    raise AuthenticationError("Invalid API key.")


# ---------------------------------------------------------
# Typed Dependencies
# ---------------------------------------------------------
async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """Ensures the current user is active (not deleted)."""
    if hasattr(current_user, "is_deleted") and current_user.is_deleted:
        raise AuthenticationError("User account is deactivated.")
    return current_user


def require_role(minimum_role: UserRole):
    """
    Dependency factory that enforces a minimum role.

    Usage:
        @router.post("/", dependencies=[Depends(require_role(UserRole.DEVELOPER))])
    """

    async def role_checker(current_user=Depends(get_current_active_user)):
        user_role = UserRole(current_user.role)
        if not user_role.has_at_least(minimum_role):
            raise InsufficientPermissionsError(
                f"Requires at least '{minimum_role.value}' role."
            )
        return current_user

    return role_checker


CurrentUser = Annotated[object, Depends(get_current_active_user)]
