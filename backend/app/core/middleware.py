import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.logging import log_event
from app.core.observability import record_http_request


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex}")
    request.state.request_id = request_id
    started = time.perf_counter()

    response = await call_next(request)
    duration_seconds = time.perf_counter() - started
    duration_ms = round(duration_seconds * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    record_http_request(request.method, request.url.path, response.status_code, duration_seconds)

    log_event(
        "http_request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response
