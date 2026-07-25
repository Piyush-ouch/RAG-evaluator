"""
Application Event Bus

Lightweight in-process event bus for decoupled domain events.
Used for audit logging, notifications, and side-effects that
shouldn't be tightly coupled to the main business logic.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)

# Type alias for event handlers
EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """
    Simple async event bus for domain events.

    Usage:
        event_bus = EventBus()
        event_bus.subscribe("user.created", send_welcome_email)
        event_bus.subscribe("user.created", create_audit_log)
        await event_bus.publish("user.created", user_id="123", email="user@example.com")
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register a handler for an event."""
        self._handlers[event_name].append(handler)
        logger.debug("event_handler_registered", event=event_name, handler=handler.__name__)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a handler for an event."""
        self._handlers[event_name].remove(handler)

    async def publish(self, event_name: str, **kwargs: Any) -> None:
        """
        Publish an event to all registered handlers.

        Handlers run concurrently but failures are isolated —
        one handler failing won't prevent others from executing.
        """
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            return

        logger.info("event_published", event=event_name, handler_count=len(handlers))

        tasks = []
        for handler in handlers:
            tasks.append(self._safe_execute(handler, event_name, **kwargs))

        await asyncio.gather(*tasks)

    async def _safe_execute(
        self,
        handler: EventHandler,
        event_name: str,
        **kwargs: Any,
    ) -> None:
        """Execute a handler with error isolation."""
        try:
            await handler(**kwargs)
        except Exception:
            logger.exception(
                "event_handler_failed",
                event=event_name,
                handler=handler.__name__,
            )


# Module-level singleton
event_bus = EventBus()
