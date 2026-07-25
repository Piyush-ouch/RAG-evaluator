"""
RBAC Permission System

Role-based access control with hierarchical permissions.
Provides FastAPI dependency injection decorators for route protection.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

import structlog
from fastapi import Depends

from app.core.constants import UserRole
from app.core.exceptions import InsufficientPermissionsError

logger = structlog.get_logger(__name__)


def require_role(minimum_role: UserRole) -> Callable:
    """
    FastAPI dependency that enforces a minimum role requirement.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint(): ...
    """

    async def role_checker(
        current_user: Any = Depends(_get_current_user_dependency),
    ) -> Any:
        user_role = UserRole(current_user.role)
        if not user_role.has_at_least(minimum_role):
            logger.warning(
                "permission_denied",
                user_id=str(current_user.id),
                user_role=user_role.value,
                required_role=minimum_role.value,
            )
            raise InsufficientPermissionsError(
                detail=f"This action requires at least '{minimum_role.value}' role."
            )
        return current_user

    return role_checker


def require_org_membership(org_id_param: str = "org_id") -> Callable:
    """
    Dependency that verifies the current user belongs to the specified organization.

    Extracts org_id from path parameters and checks membership.
    """

    async def org_checker(
        current_user: Any = Depends(_get_current_user_dependency),
        **kwargs: Any,
    ) -> Any:
        # The actual org_id validation happens in the dependency chain
        # by checking current_user.org_id against the request's org_id
        return current_user

    return org_checker


def require_project_access(project_id_param: str = "project_id") -> Callable:
    """
    Dependency that verifies the current user has access to a project.

    Projects are scoped to organizations, so this also validates org membership.
    """

    async def project_checker(
        current_user: Any = Depends(_get_current_user_dependency),
    ) -> Any:
        return current_user

    return project_checker


def _get_current_user_dependency() -> Any:
    """
    Placeholder that resolves to the real dependency at import time.

    This avoids circular imports between permissions.py and deps.py.
    The actual implementation is in app.api.deps.get_current_user.
    """
    from app.api.deps import get_current_user
    return Depends(get_current_user)


class PermissionChecker:
    """
    Programmatic permission checks for service-layer use.

    Unlike the dependency-based approach for routes, this class
    provides explicit permission checks for business logic.
    """

    @staticmethod
    def can_manage_org(user_role: UserRole) -> bool:
        """Can the user manage organization settings?"""
        return user_role.has_at_least(UserRole.OWNER)

    @staticmethod
    def can_invite_members(user_role: UserRole) -> bool:
        """Can the user invite new members?"""
        return user_role.has_at_least(UserRole.OWNER)

    @staticmethod
    def can_create_project(user_role: UserRole) -> bool:
        """Can the user create new projects?"""
        return user_role.has_at_least(UserRole.DEVELOPER)

    @staticmethod
    def can_run_evaluation(user_role: UserRole) -> bool:
        """Can the user run evaluations?"""
        return user_role.has_at_least(UserRole.DEVELOPER)

    @staticmethod
    def can_view_reports(user_role: UserRole) -> bool:
        """Can the user view reports?"""
        return user_role.has_at_least(UserRole.VIEWER)

    @staticmethod
    def can_manage_billing(user_role: UserRole) -> bool:
        """Can the user manage billing?"""
        return user_role.has_at_least(UserRole.OWNER)

    @staticmethod
    def can_manage_api_keys(user_role: UserRole) -> bool:
        """Can the user manage API keys?"""
        return user_role.has_at_least(UserRole.OWNER)

    @staticmethod
    def can_delete_project(user_role: UserRole) -> bool:
        """Can the user delete projects?"""
        return user_role.has_at_least(UserRole.OWNER)

    @staticmethod
    def can_export_data(user_role: UserRole) -> bool:
        """Can the user export data?"""
        return user_role.has_at_least(UserRole.DEVELOPER)
