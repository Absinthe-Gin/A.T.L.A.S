from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.ai.dependencies import get_orchestrator
from app.modules.ai.orchestrator import Orchestrator
from app.modules.ai.schemas import ChatRequest, ChatResponse, ToolCallSummary
from app.modules.users.public import CurrentUser, get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


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
    )
