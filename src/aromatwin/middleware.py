import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from aromatwin.security import redact_sensitive_fields

LOGGER = logging.getLogger("aromatwin.access")


class SecurityAndLoggingMiddleware(BaseHTTPMiddleware):
    """Attach request metadata and safe, structured access logging."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        LOGGER.info(
            "request_complete %s",
            redact_sensitive_fields(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": dict(request.query_params),
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            ),
        )
        return response
