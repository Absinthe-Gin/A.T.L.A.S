from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.modules.memory.repository import (
    ConversationRepository,
    MemoryRepository,
    MessageRepository,
)
from app.modules.memory.service import ConversationService, MemoryService


def get_conversation_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConversationService:
    return ConversationService(
        session=session,
        conversations=ConversationRepository(session),
        messages=MessageRepository(session),
    )


def get_memory_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MemoryService:
    return MemoryService(MemoryRepository(session))
