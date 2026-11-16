"""Proposed changes and their confirmation by the user (CLAUDE.md, section 6.2)."""

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.request_context import get_request_id
from app.infrastructure.database.base import utc_now
from app.modules.ai.models import PendingAction, PendingActionStatus
from app.modules.ai.tools.executor import ToolExecutor
from app.modules.memory.public import ConversationService, MessageRole
from app.shared.tools import ToolContext

logger = logging.getLogger(__name__)


class PendingActionNotFoundError(NotFoundError):
    code = "pending_action_not_found"
    message = "Không tìm thấy đề xuất cần xác nhận."


class PendingActionResolvedError(ConflictError):
    code = "pending_action_resolved"
    message = "Đề xuất này đã được xử lý."


class PendingActionData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    tool_name: str
    summary: str
    status: PendingActionStatus
    result: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    resolved_at: datetime | None


class PendingActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, action: PendingAction) -> PendingAction:
        self._session.add(action)
        await self._session.flush()
        return action

    async def get_for_user(self, action_id: uuid.UUID, user_id: uuid.UUID) -> PendingAction | None:
        statement = select(PendingAction).where(
            PendingAction.id == action_id, PendingAction.user_id == user_id
        )
        return await self._session.scalar(statement)

    async def list_for_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Sequence[PendingAction]:
        statement = (
            select(PendingAction)
            .where(
                PendingAction.conversation_id == conversation_id,
                PendingAction.user_id == user_id,
            )
            .order_by(PendingAction.created_at)
        )
        return (await self._session.scalars(statement)).all()


class PendingActionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: PendingActionRepository,
        executor: ToolExecutor,
        conversations: ConversationService,
    ) -> None:
        self._session = session
        self._repository = repository
        self._executor = executor
        self._conversations = conversations

    async def propose(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        tool_name: str,
        arguments: dict[str, Any],
        summary: str,
    ) -> PendingActionData:
        action = await self._repository.add(
            PendingAction(
                user_id=user_id,
                conversation_id=conversation_id,
                tool_name=tool_name,
                arguments=arguments,
                summary=summary,
                status=PendingActionStatus.PENDING,
            )
        )
        await self._session.commit()
        logger.info("Action proposed", extra={"action_id": str(action.id), "tool_name": tool_name})
        return PendingActionData.model_validate(action)

    async def list_for_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[PendingActionData]:
        """Every proposal made in one conversation, oldest first, so a reopened chat shows them."""
        actions = await self._repository.list_for_conversation(conversation_id, user_id)
        return [PendingActionData.model_validate(action) for action in actions]

    async def confirm(self, action_id: uuid.UUID, user_id: uuid.UUID) -> PendingActionData:
        """Run the proposed change. A refusal by the module is recorded, not raised."""
        action = await self._pending(action_id, user_id)
        context = ToolContext(
            user_id=user_id, conversation_id=action.conversation_id, request_id=get_request_id()
        )
        result = await self._executor.execute_confirmed(action.tool_name, action.arguments, context)

        if result.succeeded:
            action.status = PendingActionStatus.CONFIRMED
            action.result = result.output
            note = f"Người dùng đã xác nhận và hệ thống đã thực hiện: {action.summary}"
        else:
            action.status = PendingActionStatus.FAILED
            action.error_code = result.error_code
            action.error_message = result.error_message
            note = f"Người dùng đã xác nhận nhưng không thực hiện được: {action.summary}"
        return await self._resolve(action, note)

    async def cancel(self, action_id: uuid.UUID, user_id: uuid.UUID) -> PendingActionData:
        action = await self._pending(action_id, user_id)
        action.status = PendingActionStatus.CANCELLED
        return await self._resolve(action, f"Người dùng đã hủy đề xuất: {action.summary}")

    async def _pending(self, action_id: uuid.UUID, user_id: uuid.UUID) -> PendingAction:
        action = await self._repository.get_for_user(action_id, user_id)
        if action is None:
            raise PendingActionNotFoundError()
        if action.status is not PendingActionStatus.PENDING:
            raise PendingActionResolvedError()
        return action

    async def _resolve(self, action: PendingAction, note: str) -> PendingActionData:
        action.resolved_at = utc_now()
        await self._session.commit()
        # Later turns must know what happened, so the outcome joins the conversation.
        await self._conversations.append_message(
            action.conversation_id,
            MessageRole.SYSTEM,
            note,
            meta={"action_id": str(action.id), "status": action.status.value},
        )
        logger.info(
            "Action resolved",
            extra={
                "action_id": str(action.id),
                "tool_name": action.tool_name,
                "status": action.status.value,
                "error_code": action.error_code,
            },
        )
        return PendingActionData.model_validate(action)
