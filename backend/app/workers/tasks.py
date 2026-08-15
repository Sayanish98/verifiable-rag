import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.integrations.mongodb import create_mongodb
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.schemas.document import DocumentStatus
from app.workers.celery_app import celery_app
from app.workers.ingestion_worker import IngestionWorker
from vectorstore import VectorStore


@celery_app.task(
    bind=True,
    max_retries=3,
)
def ingest_document(self, document_id: str, filename: str, file_path: str) -> dict:
    """Celery entry point for durable document ingestion.

    The async worker logic is reused here so FastAPI and Celery share one ingestion implementation.
    """
    path = Path(file_path)
    try:
        return asyncio.run(_ingest_document(document_id, filename, path, self.request.retries))
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            path.unlink(missing_ok=True)
            return {"document_id": document_id, "status": DocumentStatus.failed, "error": str(exc)}
        raise self.retry(exc=exc, countdown=min(60, 2**self.request.retries))


async def _ingest_document(document_id: str, filename: str, file_path: Path, retry_count: int) -> dict:
    settings = get_settings()
    database = await create_mongodb(settings)
    documents = DocumentRepository(database)
    vectors = VectorRepository(VectorStore(settings.vector_db_path))
    worker = IngestionWorker(documents, vectors)
    try:
        await worker.ingest(document_id, filename, file_path, raise_on_failure=True)
        document = await documents.get(document_id)
        return {
            "document_id": document_id,
            "status": document.status if document else DocumentStatus.ready,
            "retry_count": retry_count,
        }
    except Exception:
        await documents.update_status(document_id, DocumentStatus.failed, error_code="WORKER_CRASHED")
        raise
