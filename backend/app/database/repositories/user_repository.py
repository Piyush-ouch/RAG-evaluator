"""
User Repository

Domain repository handling persistence and lookup operations for User entities.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        """Retrieve user by unique email address."""
        return await self.find_one(User.email == email.strip().lower())

    async def find_by_org_id(self, org_id: uuid.UUID) -> Sequence[User]:
        """Retrieve all active users belonging to an organization."""
        return await self.find_many(User.org_id == org_id)

    async def find_by_auth_provider(self, provider: str, provider_id: str) -> User | None:
        """Find OAuth user by provider name and provider account ID."""
        return await self.find_one(
            User.auth_provider == provider,
            User.auth_provider_id == provider_id,
        )
