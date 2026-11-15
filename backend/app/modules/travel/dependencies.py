from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.external import ExternalServices
from app.modules.travel.info import TravelInfoService
from app.modules.travel.repository import TravelRepository
from app.modules.travel.service import TravelPlanService


def build_plan_service(session: AsyncSession) -> TravelPlanService:
    return TravelPlanService(session, TravelRepository(session))


def get_plan_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TravelPlanService:
    return build_plan_service(session)


def get_info_service(request: Request) -> TravelInfoService:
    external: ExternalServices = request.app.state.external
    return TravelInfoService(external)
