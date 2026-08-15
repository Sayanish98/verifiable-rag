from app.core.config import Settings
from app.core.logging import log_event


def configure_opentelemetry(settings: Settings) -> None:
    if not settings.otel_exporter_otlp_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "verifiable-rag-api"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)))
        trace.set_tracer_provider(provider)
        log_event("opentelemetry_configured", endpoint=settings.otel_exporter_otlp_endpoint)
    except Exception as exc:
        log_event("opentelemetry_unavailable", error=str(exc))

