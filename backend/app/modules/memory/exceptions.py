from app.core.exceptions import NotFoundError


class ConversationNotFoundError(NotFoundError):
    code = "conversation_not_found"
    message = "Không tìm thấy cuộc hội thoại."
