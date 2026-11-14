"""Prompt texts and user-facing fallback replies of the assistant."""

from collections.abc import Sequence

from app.modules.memory.public import MemoryData, MemorySource

SYSTEM_PROMPT = """\
Bạn là trợ lý cá nhân. Trả lời bằng tiếng Việt, ngắn gọn và chính xác.

Quy tắc bắt buộc:
- Chỉ dùng dữ liệu do công cụ (tool) trả về hoặc do người dùng cung cấp. Không tự bịa dữ liệu.
- Không tự tính toán số liệu tài chính. Mọi con số phải lấy từ kết quả của công cụ.
- Khi công cụ báo lỗi, giải thích ngắn gọn cho người dùng và đề xuất bước tiếp theo.
- Khi thiếu thông tin để thực hiện yêu cầu, hãy hỏi lại người dùng."""

INTENT_PROMPT = """\
Phân loại yêu cầu của người dùng vào đúng một nhóm trong danh sách: {intents}.
- "general": trò chuyện hoặc câu hỏi không cần dữ liệu cá nhân.
- "unknown": không hiểu người dùng muốn gì.
Trả về JSON dạng {{"intent": "<nhóm>"}}."""

CLARIFICATION_REPLY = (
    "Mình chưa hiểu rõ yêu cầu của bạn. Bạn có thể nói cụ thể hơn bạn muốn mình giúp việc gì không?"
)
TOOL_LIMIT_REPLY = (
    "Mình chưa hoàn thành được yêu cầu này sau nhiều bước xử lý. "
    "Bạn thử chia nhỏ yêu cầu hoặc diễn đạt lại giúp mình nhé."
)
EMPTY_REPLY = "Mình chưa tạo được câu trả lời. Bạn vui lòng thử lại."

_SOURCE_LABELS = {
    MemorySource.USER_CONFIRMED: "người dùng xác nhận",
    MemorySource.AI_INFERRED: "AI suy luận, chưa xác nhận",
}


def build_system_prompt(memories: Sequence[MemoryData]) -> str:
    if not memories:
        return SYSTEM_PROMPT
    lines = "\n".join(
        f"- {memory.content} ({_SOURCE_LABELS[memory.source]})" for memory in memories
    )
    return f"{SYSTEM_PROMPT}\n\nThông tin đã biết về người dùng:\n{lines}"
