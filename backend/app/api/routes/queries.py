import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.schemas.query import GraphStateResponse, LegacyQueryRequest, QueryRequest, QueryResponse, ResumeRequest
from app.services.query_service import QueryService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: Request,
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    return await service.execute(payload, request.state.request_id)


@router.post("/stream")
async def stream_query_documents(
    request: Request,
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    async def events():
        async for event_name, data in service.stream(payload, request.state.request_id):
            yield f"event: {event_name}\ndata: {json.dumps(data)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/resume", response_model=QueryResponse)
async def resume_query_run(
    request: Request,
    payload: ResumeRequest,
    service: QueryService = Depends(get_query_service),
):
    return await service.resume(
        payload.thread_id,
        request.state.request_id,
        approved=payload.approved,
        comment=payload.comment,
    )


@router.get("/{thread_id}/state", response_model=GraphStateResponse)
async def get_query_run_state(
    thread_id: str,
    service: QueryService = Depends(get_query_service),
):
    return await service.get_state(thread_id)


@router.post("/legacy")
async def legacy_query_documents(
    request: Request,
    payload: LegacyQueryRequest,
    service: QueryService = Depends(get_query_service),
):
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
