from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import get_document_service, get_query_service
from app.api.routes import documents, evaluations, health, queries
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.middleware import request_context_middleware
from app.core.observability import LangfuseTracer
from app.integrations.langgraph_checkpointer import close_langgraph_checkpointer, create_langgraph_checkpointer
from app.integrations.mongodb import create_mongodb
from app.integrations.otel import configure_opentelemetry
from app.integrations.redis_client import create_redis_cache
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DeleteDocumentRequest
from app.schemas.error import ErrorResponse
from app.schemas.query import LegacyQueryRequest, QueryRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    configure_opentelemetry(settings)
    database = await create_mongodb(settings)
    app.state.document_repository = DocumentRepository(database)
    app.state.redis_cache = await create_redis_cache(settings)
    app.state.langgraph_checkpointer, app.state.langgraph_checkpointer_context = await create_langgraph_checkpointer(settings)
    app.state.langfuse_tracer = LangfuseTracer.from_settings(settings)
    yield
    await close_langgraph_checkpointer(getattr(app.state, "langgraph_checkpointer_context", None))


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        lifespan=lifespan,
        responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    app.middleware("http")(request_context_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(documents.router, prefix=settings.api_v1_prefix)
    app.include_router(queries.router, prefix=settings.api_v1_prefix)
    app.include_router(evaluations.router, prefix=settings.api_v1_prefix)
    _register_legacy_routes(app)
    _register_exception_handlers(app)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(code=exc.code, message=exc.message, request_id=request_id).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                code="VALIDATION_ERROR",
                message=str(exc.errors()[0].get("msg", "Request validation failed")),
                request_id=request_id,
            ).model_dump(),
        )


def _register_legacy_routes(app: FastAPI) -> None:
    @app.post("/upload")
    async def legacy_upload(request: Request, files: list[UploadFile] = File(...)):
        service = get_document_service(request)
        processed = []
        skipped = []
        for file in files:
            try:
                response = await service.upload(file, request.state.request_id)
                processed.append(response.filename)
            except AppError:
                skipped.append(file.filename)
        message_parts = []
        if processed:
            message_parts.append(f"{len(processed)} file(s) accepted for ingestion")
        if skipped:
            message_parts.append(f"{len(skipped)} file(s) skipped (already uploaded): {', '.join(skipped)}")
        return {"status": "success", "message": ". ".join(message_parts), "processed": processed, "skipped": skipped}

    @app.post("/query")
    async def legacy_query(request: Request, payload: LegacyQueryRequest):
        service = get_query_service(request)
        response = await service.execute(
            QueryRequest(query=payload.question, conversation_history=payload.conversation_history or []),
            request.state.request_id,
        )
        return {
            "answer": response.answer,
            "evidence": [
                {"doc_name": citation.document_name, "page_number": citation.page, "text": citation.snippet}
                for citation in response.citations
            ],
        }

    @app.delete("/delete-document")
    async def legacy_delete(request: Request, payload: DeleteDocumentRequest):
        service = get_document_service(request)
        deleted = await service.delete_by_name(payload.doc_name)
        return {"status": "success", "message": f"Deleted {deleted} chunks from '{payload.doc_name}'"}


app = create_app()
