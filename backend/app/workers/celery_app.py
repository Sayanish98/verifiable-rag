from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "verifiable_rag",
    broker=settings.celery_broker_url or settings.redis_url or "redis://redis:6379/0",
    backend=settings.celery_result_backend or settings.redis_url or "redis://redis:6379/1",
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="document_ingestion",
    task_routes={"app.workers.tasks.ingest_document": {"queue": "document_ingestion"}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

