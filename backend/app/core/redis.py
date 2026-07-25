"""
Redis Client

Async Redis client with connection pooling, health checks,
and utility methods for caching, rate limiting, and pub/sub.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Async Redis client wrapper.

    Provides a high-level interface for common Redis operations
    with connection management and error handling.
    """

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None
        self._cache_client: aioredis.Redis | None = None

    async def initialize(self) -> None:
        """Initialize Redis connections."""
        settings = get_settings()
        self._client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        self._cache_client = aioredis.from_url(
            settings.redis_url.rsplit("/", 1)[0] + f"/{settings.redis_cache_db}",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("redis_initialized")

    async def close(self) -> None:
        """Close all Redis connections."""
        if self._client:
            await self._client.close()
        if self._cache_client:
            await self._cache_client.close()
        logger.info("redis_closed")

    @property
    def client(self) -> aioredis.Redis:
        """Get the primary Redis client."""
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client

    @property
    def cache(self) -> aioredis.Redis:
        """Get the cache-specific Redis client."""
        if self._cache_client is None:
            raise RuntimeError("Redis cache not initialized.")
        return self._cache_client

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return await self.client.ping()
        except Exception:
            return False

    # ---------------------------------------------------------
    # Cache Operations
    # ---------------------------------------------------------

    async def cache_get(self, key: str) -> str | None:
        """Get a cached value by key."""
        return await self.cache.get(key)

    async def cache_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int = 300,
    ) -> None:
        """Set a cached value with TTL."""
        await self.cache.set(key, value, ex=ttl_seconds)

    async def cache_delete(self, key: str) -> None:
        """Delete a cached value."""
        await self.cache.delete(key)

    async def cache_delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern."""
        async for key in self.cache.scan_iter(match=pattern, count=100):
            await self.cache.delete(key)

    # ---------------------------------------------------------
    # Rate Limiting (Token Bucket)
    # ---------------------------------------------------------

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Check rate limit using a sliding window counter.

        Returns:
            tuple: (allowed: bool, remaining: int)
        """
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        current = results[0]
        remaining = max(0, max_requests - current)
        allowed = current <= max_requests

        return allowed, remaining

    # ---------------------------------------------------------
    # Token Blacklist (for JWT logout)
    # ---------------------------------------------------------

    async def blacklist_token(self, jti: str, ttl_seconds: int) -> None:
        """Add a token JTI to the blacklist."""
        await self.client.set(f"blacklist:{jti}", "1", ex=ttl_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        return await self.client.exists(f"blacklist:{jti}") > 0

    # ---------------------------------------------------------
    # Pub/Sub (for real-time evaluation progress)
    # ---------------------------------------------------------

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a Redis channel."""
        await self.client.publish(channel, message)

    def subscribe(self, channel: str) -> aioredis.client.PubSub:
        """Subscribe to a Redis channel."""
        pubsub = self.client.pubsub()
        return pubsub


# Module-level singleton
redis_client = RedisClient()
