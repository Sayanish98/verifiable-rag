from datetime import datetime, timezone

import pytest

from app.schemas.document import DocumentMetadata, DocumentStatus
from app.workers.ingestion_worker import IngestionWorker


class FakeDocumentRepository:
    def __init__(self):
        self.document = DocumentMetadata(
            id="doc-1",
            filename="failed.pdf",
            checksum="sha",
            status=DocumentStatus.pending,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def update_status(self, document_id, status, **kwargs):
        self.document = self.document.model_copy(
            update={
                "status": status,
                "error_code": kwargs.get("error_code"),
                "updated_at": datetime.now(timezone.utc),
            }
        )


class FakeVectorRepository:
    async def add_chunk(self, chunk):
        raise AssertionError("vectors should not be written when parsing fails")


@pytest.mark.asyncio
async def test_ingestion_failure_marks_document_failed(monkeypatch, tmp_path):
    documents = FakeDocumentRepository()

    def fail_pdf_parse(path, filename):
        raise RuntimeError("ocr failed")

    monkeypatch.setattr("app.workers.ingestion_worker.extract_text_from_pdf", fail_pdf_parse)
    pdf_path = tmp_path / "failed.pdf"
    pdf_path.write_bytes(b"%PDF")

    worker = IngestionWorker(documents, FakeVectorRepository())
    await worker.ingest("doc-1", "failed.pdf", pdf_path)

    assert documents.document.status == DocumentStatus.failed
    assert documents.document.error_code == "INGESTION_FAILED"

