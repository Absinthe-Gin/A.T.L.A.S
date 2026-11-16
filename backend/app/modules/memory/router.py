import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.memory.dependencies import get_conversation_service
from app.modules.memory.schemas import ConversationMessage, ConversationRename, ConversationSummary
from app.modules.memory.service import ConversationService
from app.modules.users.public import CurrentUser, get_current_user
from app.shared.schemas import Page

User = Annotated[CurrentUser, Depends(get_current_user)]
Conversations = Annotated[ConversationService, Depends(get_conversation_service)]

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=Page[ConversationSummary])
async def list_conversations(
    user: User,
    conversations: Conversations,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ConversationSummary]:
    """Conversations, most recently active first."""
    return await conversations.list_conversations(user.id, limit=limit, offset=offset)


@router.get("/{conversation_id}/messages", response_model=Page[ConversationMessage])
async def list_messages(
    conversation_id: uuid.UUID,
    user: User,
    conversations: Conversations,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ConversationMessage]:
    """Messages a person reads, **newest first**; `offset` pages back in time."""
    return await conversations.list_messages(conversation_id, user.id, limit=limit, offset=offset)


@router.patch("/{conversation_id}", response_model=ConversationSummary)
async def rename_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationRename,
    user: User,
    conversations: Conversations,
) -> ConversationSummary:
    return await conversations.rename_conversation(conversation_id, user.id, payload.title)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID, user: User, conversations: Conversations
) -> Response:
    """Delete the conversation with its messages and proposals. Long-term memories stay."""
    await conversations.delete_conversation(conversation_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
