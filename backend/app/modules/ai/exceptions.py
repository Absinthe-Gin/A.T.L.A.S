from app.core.exceptions import ExternalServiceError, ExternalServiceUnavailableError


class LLMNotConfiguredError(ExternalServiceUnavailableError):
    code = "llm_not_configured"
    message = "Chưa cấu hình model AI. Hãy đặt OLLAMA_MODEL trong file .env của Backend."


class LLMInvalidResponseError(ExternalServiceError):
    code = "llm_invalid_response"
    message = "Model AI trả về dữ liệu không hợp lệ."


class ToolRegistrationError(Exception):
    """A tool is defined incorrectly. This is a programming error raised at startup."""
