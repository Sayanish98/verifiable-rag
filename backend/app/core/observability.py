import time
from contextlib import asynccontextmanager
from typing import Any

from app.core.logging import log_event

try:
    from prometheus_client import Counter, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except Exception:
    Counter = Histogram = None
    PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import trace

    OTEL_AVAILABLE = True
except Exception:
    trace = None
    OTEL_AVAILABLE = False


if PROMETHEUS_AVAILABLE:
    HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    HTTP_REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "path"])
    AGENT_RUNS_TOTAL = Counter("agent_runs_total", "Total agent runs", ["status"])
    AGENT_RUN_DURATION = Histogram("agent_run_duration_seconds", "Agent run latency", ["status"])
    AGENT_RETRIES_TOTAL = Counter("agent_retries_total", "Agent graph retries", ["node"])
    LLM_REQUESTS_TOTAL = Counter("llm_requests_total", "Total LLM requests", ["status"])
    LLM_REQUEST_DURATION = Histogram("llm_request_duration_seconds", "LLM request latency", ["status"])
    RETRIEVAL_DURATION = Histogram("retrieval_duration_seconds", "Retrieval latency")
    RETRIEVAL_RESULTS = Histogram("retrieval_results_count", "Retrieved result count")
    RETRIEVAL_EMPTY_TOTAL = Counter("retrieval_empty_total", "Empty retrieval responses")
    CACHE_HITS_TOTAL = Counter("cache_hits_total", "Query cache hits")
    CACHE_MISSES_TOTAL = Counter("cache_misses_total", "Query cache misses")


def metrics_response() -> bytes:
    if not PROMETHEUS_AVAILABLE:
        return b"# prometheus_client is not installed\n"
    return generate_latest()


def record_http_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    if PROMETHEUS_AVAILABLE:
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=str(status)).inc()
        HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(duration_seconds)


def record_cache_hit(hit: bool) -> None:
    if PROMETHEUS_AVAILABLE:
        (CACHE_HITS_TOTAL if hit else CACHE_MISSES_TOTAL).inc()


def record_agent_retry(node: str) -> None:
    if PROMETHEUS_AVAILABLE:
        AGENT_RETRIES_TOTAL.labels(node=node).inc()


def record_retrieval(duration_seconds: float, results_count: int) -> None:
    if PROMETHEUS_AVAILABLE:
        RETRIEVAL_DURATION.observe(duration_seconds)
        RETRIEVAL_RESULTS.observe(results_count)
        if results_count == 0:
            RETRIEVAL_EMPTY_TOTAL.inc()


@asynccontextmanager
async def observe_span(name: str, **metadata: Any):
    """Record a privacy-safe app span.

    Metadata should contain identifiers and counts only, never raw medical text.
    """
    started = time.perf_counter()
    tracer = trace.get_tracer("verifiable-rag") if OTEL_AVAILABLE else None
    span_cm = tracer.start_as_current_span(name) if tracer else None
    span = span_cm.__enter__() if span_cm else None
    try:
        if span:
            for key, value in metadata.items():
                if value is not None:
                    span.set_attribute(key, value)
        yield span
        status = "success"
    except Exception as exc:
        status = "error"
        if span:
            span.record_exception(exc)
        raise
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        if span_cm:
            span_cm.__exit__(None, None, None)
        log_event("span_completed", span=name, duration_ms=duration_ms, status=status, **metadata)


class LangfuseTracer:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._client = None

    @classmethod
    def from_settings(cls, settings):
        enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
        tracer = cls(enabled)
        if enabled:
            try:
                from langfuse import Langfuse

                tracer._client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except Exception as exc:
                log_event("langfuse_unavailable", error=str(exc))
                tracer.enabled = False
        return tracer

    def trace_agent_step(self, name: str, *, request_id: str, thread_id: str, metadata: dict[str, Any]) -> None:
        if not self.enabled or self._client is None:
            return
        try:
            self._client.trace(
                name=name,
                id=f"{request_id}:{name}",
                session_id=thread_id,
                metadata={**metadata, "request_id": request_id, "thread_id": thread_id},
            )
        except Exception as exc:
            log_event("langfuse_trace_failed", step=name, error=str(exc))

