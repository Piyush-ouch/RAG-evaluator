"""
Request ID Middleware

Assigns a unique X-Request-ID to every request for distributed tracing.
If the client sends one, it's preserved; otherwise a UUID is generated.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for accessing request_id anywhere in the call chain
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects X-Request-ID into request state and response headers."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Use client-provided ID or generate a new one
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context var for access by logging, services, etc.
        request_id_var.set(req_id)
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id

        return response
