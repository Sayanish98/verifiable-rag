import asyncio
import hashlib
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.schemas.document import DocumentMetadata, UploadDocumentResponse
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
        document = await self.documents.create_pending(file.filename, checksum)
        path = self._upload_path(document.id, file.filename)
        await asyncio.to_thread(path.write_bytes, contents)

        # A production deployment can replace this with Celery: FastAPI -> Redis -> worker.
        asyncio.create_task(self.worker.ingest(document.id, file.filename, path))

        return UploadDocumentResponse(
            id=document.id,
            filename=document.filename,
            checksum=document.checksum,
            status=document.status,
            request_id=request_id,
            message="Document accepted for background ingestion",
        )

    async def get(self, document_id: str) -> DocumentMetadata | None:
        return await self.documents.get(document_id)

    async def list(self) -> list[DocumentMetadata]:
        return await self.documents.list()

    async def delete_by_name(self, doc_name: str) -> int:
        return await self.vectors.delete_document(doc_name)

    def _upload_path(self, document_id: str, filename: str) -> Path:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return self.settings.upload_path / f"{document_id}_{safe_name}"

