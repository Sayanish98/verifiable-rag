from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_evaluation_service
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/golden")
async def run_golden_dataset(
    request: Request,
    service: EvaluationService = Depends(get_evaluation_service),
):
    return await service.run_golden_dataset(request.state.request_id)

