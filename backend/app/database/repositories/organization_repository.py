"""
Organization Repository

Domain repository handling persistence and tenant lookup operations for Organization entities.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.models.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def find_by_slug(self, slug: str) -> Organization | None:
        """Find an organization by unique URL slug."""
        return await self.find_one(Organization.slug == slug.strip().lower())

    async def find_by_stripe_customer_id(self, stripe_customer_id: str) -> Organization | None:
        """Find an organization by Stripe customer identifier."""
        return await self.find_one(Organization.stripe_customer_id == stripe_customer_id)
