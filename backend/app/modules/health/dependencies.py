from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.modules.ai.public import LLMProvider, get_llm_provider
from app.modules.health.service import HealthService


def get_health_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> HealthService:
    return HealthService(session=session, settings=request.app.state.settings, llm=llm)
