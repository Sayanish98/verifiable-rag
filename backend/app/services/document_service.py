import asyncio
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import QueueUnavailableError
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.schemas.document import DocumentMetadata, DocumentStatus, UploadDocumentResponse
from app.workers.ingestion_worker import IngestionWorker


class DocumentService:
    def __init__(self, settings: Settings, documents: DocumentRepository, vectors: VectorRepository):
        self.settings = settings
        self.documents = documents
        self.vectors = vectors
        self.worker = IngestionWorker(documents, vectors)

    async def upload(self, file: UploadFile, request_id: str) -> UploadDocumentResponse:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported")

        contents = await file.read()
        checksum = hashlib.sha256(contents).hexdigest()
        ingestion_job_id = f"ingest_{uuid4().hex}"
        document = await self.documents.create_pending(file.filename, checksum, ingestion_job_id=ingestion_job_id)
        path = self._upload_path(document.id, file.filename)
        await asyncio.to_thread(path.write_bytes, contents)

        if self.settings.use_celery_ingestion:
            try:
                await self._enqueue_celery_ingestion(document.id, file.filename, path, ingestion_job_id)
            except Exception as exc:
                await self.documents.update_status(document.id, DocumentStatus.failed, error_code="ENQUEUE_FAILED")
                await asyncio.to_thread(lambda: path.unlink(missing_ok=True))
                raise QueueUnavailableError(str(exc)) from exc
            message = "Document accepted and queued for Celery ingestion"
        else:
            asyncio.create_task(self.worker.ingest(document.id, file.filename, path))
            message = "Document accepted for local background ingestion"

        return UploadDocumentResponse(
            id=document.id,
            filename=document.filename,
            checksum=document.checksum,
            status=document.status,
            ingestion_job_id=ingestion_job_id,
            request_id=request_id,
            message=message,
        )

    async def get(self, document_id: str) -> DocumentMetadata | None:
        return await self.documents.get(document_id)

    async def list(self, status=None, limit: int = 50) -> list[DocumentMetadata]:
        return await self.documents.list(status=status, limit=limit)

    async def list_recent_ready(self, limit: int = 20) -> list[DocumentMetadata]:
        return await self.documents.list_recent_ready(limit=limit)

    async def get_ingestion_job(self, job_id: str) -> dict:
        from app.workers.celery_app import celery_app

        def read_result():
            result = celery_app.AsyncResult(job_id)
            payload = result.result if isinstance(result.result, dict) else None
            return {
                "job_id": job_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None,
                "result": payload,
            }

        return await asyncio.to_thread(read_result)

    async def delete_by_name(self, doc_name: str) -> int:
        return await self.vectors.delete_document(doc_name)

    def _upload_path(self, document_id: str, filename: str) -> Path:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return self.settings.upload_path / f"{document_id}_{safe_name}"

    async def _enqueue_celery_ingestion(
        self,
        document_id: str,
        filename: str,
        path: Path,
        ingestion_job_id: str,
    ) -> None:
        from app.workers.tasks import ingest_document

        await asyncio.to_thread(
            ingest_document.apply_async,
            kwargs={"document_id": document_id, "filename": filename, "file_path": str(path)},
            task_id=ingestion_job_id,
            queue="document_ingestion",
        )
