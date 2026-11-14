"""Public interface of the memory module. Other modules import only from here."""

from app.modules.memory.dependencies import get_conversation_service, get_memory_service
from app.modules.memory.exceptions import ConversationNotFoundError
from app.modules.memory.models import MemorySource, MessageRole
from app.modules.memory.schemas import ConversationData, MemoryData, MessageData
from app.modules.memory.service import ConversationService, MemoryService

__all__ = [
    "ConversationData",
    "ConversationNotFoundError",
    "ConversationService",
    "MemoryData",
    "MemoryService",
    "MemorySource",
    "MessageData",
    "MessageRole",
    "get_conversation_service",
    "get_memory_service",
]
