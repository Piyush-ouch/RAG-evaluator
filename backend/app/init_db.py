"""
Database Initializer — Creates all SQLAlchemy ORM tables in PostgreSQL.
"""

import asyncio
import structlog

from app.database.session import engine
from app.database.base import Base
import app.models  # Load all models for metadata binding

logger = structlog.get_logger(__name__)


async def init_db() -> None:
    logger.info("creating_database_tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All PostgreSQL tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
