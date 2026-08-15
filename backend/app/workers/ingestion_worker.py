import asyncio
from pathlib import Path

from app.core.logging import log_event
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.schemas.document import DocumentStatus
from chunking import chunk_text
from ocr import extract_text_from_pdf


class IngestionWorker:
    def __init__(self, documents: DocumentRepository, vectors: VectorRepository):
        self.documents = documents
        self.vectors = vectors

    async def ingest(self, document_id: str, filename: str, file_path: Path, *, raise_on_failure: bool = False) -> None:
        await self.documents.update_status(document_id, DocumentStatus.processing)
        succeeded = False
        try:
            pages = await asyncio.to_thread(extract_text_from_pdf, str(file_path), filename)
            chunk_count = 0
            for page_number, page_text in pages.items():
                chunks = chunk_text(page_text, filename, page_number)
                for chunk in chunks:
                    chunk["document_id"] = document_id
                    await self.vectors.add_chunk(chunk)
                    chunk_count += 1
            await self.documents.update_status(
                document_id,
                DocumentStatus.ready,
                chunk_count=chunk_count,
                page_count=len(pages),
            )
            log_event("document_ingestion_completed", document_id=document_id, chunks=chunk_count)
            succeeded = True
        except Exception as exc:
            await self.documents.update_status(document_id, DocumentStatus.failed, error_code="INGESTION_FAILED")
            log_event("document_ingestion_failed", document_id=document_id, error=str(exc))
            if raise_on_failure:
                raise
        finally:
            if succeeded or not raise_on_failure:
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass
