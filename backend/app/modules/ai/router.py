import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.ai.actions import PendingActionData, PendingActionService
from app.modules.ai.dependencies import get_orchestrator, get_pending_action_service
from app.modules.ai.orchestrator import Orchestrator
from app.modules.ai.schemas import ChatRequest, ChatResponse, PendingActionView, ToolCallSummary
from app.modules.users.public import CurrentUser, get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


def _view(action: PendingActionData) -> PendingActionView:
    return PendingActionView(
        id=action.id,
        tool_name=action.tool_name,
        summary=action.summary,
        status=action.status.value,
        error_message=action.error_message,
        created_at=action.created_at,
    )


@router.post("", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
) -> ChatResponse:
    result = await orchestrator.handle(
        user_id=user.id, text=payload.message, conversation_id=payload.conversation_id
    )
    return ChatResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        reply=result.reply,
        intent=result.intent,
        tool_calls=[
            ToolCallSummary(name=item.tool_name, status=item.status) for item in result.tool_results
        ],
        pending_actions=[_view(action) for action in result.pending_actions],
    )


@router.get("/conversations/{conversation_id}/actions", response_model=list[PendingActionView])
async def list_conversation_actions(
    conversation_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    actions: Annotated[PendingActionService, Depends(get_pending_action_service)],
) -> list[PendingActionView]:
    """Proposals made in a conversation, oldest first; pending ones can still be confirmed."""
    return [
        _view(action) for action in await actions.list_for_conversation(conversation_id, user.id)
    ]


@router.post("/actions/{action_id}/confirm", response_model=PendingActionView)
async def confirm_action(
    action_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    actions: Annotated[PendingActionService, Depends(get_pending_action_service)],
) -> PendingActionView:
    """Carry out a change the assistant proposed. `status` tells whether it succeeded."""
    return _view(await actions.confirm(action_id, user.id))


@router.post("/actions/{action_id}/cancel", response_model=PendingActionView)
async def cancel_action(
    action_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    actions: Annotated[PendingActionService, Depends(get_pending_action_service)],
) -> PendingActionView:
    return _view(await actions.cancel(action_id, user.id))
