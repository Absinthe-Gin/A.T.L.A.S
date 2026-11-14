"""Application exception hierarchy.

Services raise these exceptions. ``app.core.error_handlers`` is the only
place that converts them into HTTP responses. Modules define their own
errors by subclassing the category that matches the failure.
"""

import logging

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """One field-level problem, used mostly for validation errors."""

    field: str | None = None
    message: str


class AppError(Exception):
    """Base class for every error the application raises on purpose."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "Đã xảy ra lỗi hệ thống."
    log_level: int = logging.ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        self.details: list[ErrorDetail] = details or []
        super().__init__(self.message)


class ValidationFailedError(AppError):
    """Input is well-formed but rejected by application-level validation."""

    status_code = 422
    code = "validation_failed"
    message = "Dữ liệu không hợp lệ."
    log_level = logging.INFO


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Không tìm thấy tài nguyên."
    log_level = logging.INFO


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Yêu cầu xung đột với trạng thái hiện tại."
    log_level = logging.INFO


class BusinessRuleError(AppError):
    status_code = 422
    code = "business_rule_violation"
    message = "Yêu cầu vi phạm quy tắc nghiệp vụ."
    log_level = logging.WARNING


class ExternalServiceError(AppError):
    """An external dependency returned an error or an invalid response."""

    status_code = 502
    code = "external_service_error"
    message = "Dịch vụ bên ngoài gặp lỗi."


class ExternalServiceTimeoutError(ExternalServiceError):
    status_code = 504
    code = "external_service_timeout"
    message = "Dịch vụ bên ngoài không phản hồi kịp thời."


class ExternalServiceUnavailableError(ExternalServiceError):
    status_code = 503
    code = "external_service_unavailable"
    message = "Dịch vụ bên ngoài hiện không sẵn sàng."
