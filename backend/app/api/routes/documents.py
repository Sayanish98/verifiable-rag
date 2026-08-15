from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.core.exceptions import AppError
from app.schemas.document import (
    DeleteDocumentRequest,
    DeleteDocumentResponse,
    DocumentMetadata,
    DocumentStatus,
    IngestionJobResponse,
    UploadDocumentResponse,
)
from app.services.document_service import DocumentService
from app.api.dependencies import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=UploadDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    try:
        return await service.upload(file, request.state.request_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentMetadata])
async def list_documents(
    status: DocumentStatus | None = None,
    limit: int = 50,
    service: DocumentService = Depends(get_document_service),
):
    return await service.list(status=status, limit=limit)


@router.get("/recent-ready", response_model=list[DocumentMetadata])
async def list_recent_ready_documents(limit: int = 20, service: DocumentService = Depends(get_document_service)):
    return await service.list_recent_ready(limit=limit)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(job_id: str, service: DocumentService = Depends(get_document_service)):
    return await service.get_ingestion_job(job_id)


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str, service: DocumentService = Depends(get_document_service)):
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("", response_model=DeleteDocumentResponse)
async def delete_document(
    request: Request,
    payload: DeleteDocumentRequest,
    service: DocumentService = Depends(get_document_service),
):
    deleted = await service.delete_by_name(payload.doc_name)
    return DeleteDocumentResponse(
        status="success",
        message=f"Deleted {deleted} chunks from '{payload.doc_name}'",
        deleted_chunks=deleted,
        request_id=request.state.request_id,
    )
