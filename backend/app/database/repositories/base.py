"""
Generic Repository Pattern

Provides a type-safe, reusable base repository with:
- CRUD operations
- Pagination
- Filtering
- Tenant-scoped queries
- Soft delete support

All concrete repositories extend BaseRepository[T] with their model type.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base, SoftDeleteMixin, TenantMixin

T = TypeVar("T", bound=Base)


class PaginatedResult(Generic[T]):
    """Container for paginated query results."""

    def __init__(
        self,
        items: Sequence[T],
        total: int,
        page: int,
        page_size: int,
    ) -> None:
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        self.has_next = page < self.total_pages
        self.has_prev = page > 1


class BaseRepository(Generic[T]):
    """
    Generic async repository providing CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(User, session)

            async def find_by_email(self, email: str) -> User | None:
                return await self.find_one(User.email == email)

    All methods that operate on tenant-scoped models require org_id.
    """

    def __init__(self, model: Type[T], session: AsyncSession) -> None:
        self._model = model
        self._session = session
        self._is_tenant_scoped = issubclass(model, TenantMixin)
        self._is_soft_deletable = issubclass(model, SoftDeleteMixin)

    # ---------------------------------------------------------
    # Query Building
    # ---------------------------------------------------------

    def _base_query(self, org_id: uuid.UUID | None = None) -> Select:
        """
        Build the base SELECT query with automatic filters.

        - Adds org_id filter for tenant-scoped models
        - Excludes soft-deleted records
        """
        stmt = select(self._model)

        # Tenant isolation
        if self._is_tenant_scoped:
            if org_id is None:
                raise ValueError(
                    f"org_id is required for tenant-scoped model {self._model.__name__}"
                )
            stmt = stmt.where(self._model.org_id == org_id)  # type: ignore

        # Soft delete filter
        if self._is_soft_deletable:
            stmt = stmt.where(self._model.deleted_at.is_(None))  # type: ignore

        return stmt

    # ---------------------------------------------------------
    # CRUD Operations
    # ---------------------------------------------------------

    async def create(self, **kwargs: Any) -> T:
        """Create a new record."""
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def get_by_id(
        self,
        id: uuid.UUID,
        org_id: uuid.UUID | None = None,
    ) -> T | None:
        """Get a record by primary key."""
        stmt = self._base_query(org_id).where(self._model.id == id)  # type: ignore
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_one(self, *filters: Any, org_id: uuid.UUID | None = None) -> T | None:
        """Find a single record matching the given filters."""
        stmt = self._base_query(org_id).where(*filters)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_many(
        self,
        *filters: Any,
        org_id: uuid.UUID | None = None,
        order_by: Any = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[T]:
        """Find multiple records matching the given filters."""
        stmt = self._base_query(org_id).where(*filters)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def paginate(
        self,
        *filters: Any,
        org_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
        order_by: Any = None,
    ) -> PaginatedResult[T]:
        """Paginated query with total count."""
        # Count query
        count_stmt = (
            select(func.count())
            .select_from(self._model)
        )

        if self._is_tenant_scoped and org_id:
            count_stmt = count_stmt.where(self._model.org_id == org_id)  # type: ignore

        if self._is_soft_deletable:
            count_stmt = count_stmt.where(self._model.deleted_at.is_(None))  # type: ignore

        if filters:
            count_stmt = count_stmt.where(*filters)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Data query
        offset = (page - 1) * page_size
        items = await self.find_many(
            *filters,
            org_id=org_id,
            order_by=order_by,
            limit=page_size,
            offset=offset,
        )

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(
        self,
        instance: T,
        **kwargs: Any,
    ) -> T:
        """Update an existing record."""
        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, instance: T) -> None:
        """
        Delete a record.

        Uses soft delete if the model supports it, otherwise hard deletes.
        """
        if self._is_soft_deletable:
            instance.deleted_at = datetime.now(timezone.utc)  # type: ignore
            await self._session.flush()
        else:
            await self._session.delete(instance)
            await self._session.flush()

    async def hard_delete(self, instance: T) -> None:
        """Permanently delete a record (bypasses soft delete)."""
        await self._session.delete(instance)
        await self._session.flush()

    async def count(
        self,
        *filters: Any,
        org_id: uuid.UUID | None = None,
    ) -> int:
        """Count records matching the given filters."""
        stmt = (
            select(func.count())
            .select_from(self._model)
        )

        if self._is_tenant_scoped and org_id:
            stmt = stmt.where(self._model.org_id == org_id)  # type: ignore

        if self._is_soft_deletable:
            stmt = stmt.where(self._model.deleted_at.is_(None))  # type: ignore

        if filters:
            stmt = stmt.where(*filters)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        *filters: Any,
        org_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if any record matches the given filters."""
        return (await self.count(*filters, org_id=org_id)) > 0
