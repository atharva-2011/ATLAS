"""Correlation ID middleware for FastAPI/Starlette applications."""

import re
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from atlas_observability.context import (
    CORRELATION_ID_HEADER,
    reset_correlation_id,
    set_correlation_id,
)

# Allow alphanumeric characters, dashes, and underscores up to 64 chars
_VALID_CORRELATION_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware ensuring every request has a correlation ID in context and response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_id = request.headers.get(CORRELATION_ID_HEADER)

        if incoming_id and _VALID_CORRELATION_RE.match(incoming_id):
            correlation_id = incoming_id
        else:
            correlation_id = str(uuid.uuid4())

        token = set_correlation_id(correlation_id)
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            reset_correlation_id(token)
