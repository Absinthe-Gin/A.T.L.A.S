from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.modules.health.dependencies import get_health_service
from app.modules.health.schemas import HealthResponse, HealthStatus
from app.modules.health.service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def get_health(
    response: Response,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    report = await service.check()
    if report.status is not HealthStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
