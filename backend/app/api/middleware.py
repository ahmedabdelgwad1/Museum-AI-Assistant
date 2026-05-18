"""CORS and request logging middleware."""

import logging
import time
import uuid

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        logger.info(
            "[%s] --> %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.exception("[%s] Unhandled exception: %s", request_id, exc)
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "[%s] <-- %s %s | status=%d | %.1fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response


def setup_cors(app, origins: list[str]) -> None:
    """Add CORS middleware to the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
