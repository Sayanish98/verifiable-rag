from fastapi import APIRouter, Response

from app.core.observability import metrics_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/metrics")
async def metrics():
    return Response(metrics_response(), media_type="text/plain; version=0.0.4")
