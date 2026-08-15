from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    pending = "PENDING"
    processing = "PROCESSING"
    ready = "READY"
    failed = "FAILED"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    checksum: str
    status: DocumentStatus
    ingestion_job_id: str | None = None
    chunk_count: int = 0
    page_count: int = 0
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadDocumentResponse(BaseModel):
    id: str
    filename: str
    checksum: str
    status: DocumentStatus
    ingestion_job_id: str | None = None
    request_id: str
    message: str


class IngestionJobResponse(BaseModel):
    job_id: str
    status: str
    ready: bool = False
    successful: bool | None = None
    failed: bool | None = None
    result: dict | None = None


class DeleteDocumentRequest(BaseModel):
    doc_name: str = Field(min_length=1, max_length=255)

class DeleteDocumentResponse(BaseModel):
    status: str
    message: str
    deleted_chunks: int
    request_id: str
