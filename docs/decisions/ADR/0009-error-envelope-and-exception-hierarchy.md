# ADR-0009: Error envelope thống nhất và phân cấp `AppError`

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

CLAUDE.md yêu cầu chuẩn hóa lỗi API, phân biệt lỗi validation, nghiệp vụ, hệ thống và dịch vụ ngoài, và không để lộ stack trace.

## Quyết định

- Mọi lỗi API trả cấu trúc `{"error": {"code", "message", "details", "request_id"}}`.
- Service ném exception kế thừa `AppError` (`app/core/exceptions.py`). Mỗi lớp mang `status_code`, `code`, `message` và mức log.
- `app/core/error_handlers.py` chuyển `AppError`, lỗi validation request và lỗi HTTP của framework thành envelope.
- Exception chưa lường trước được `RequestContextMiddleware` bắt, ghi log kèm stack trace, và trả HTTP 500 với thông điệp chung.
- Frontend chuyển mọi lỗi thành `ApiError` tại `services/api/errors.ts`.

## Hệ quả

- Router không chứa `try/except`.
- Frontend phân nhánh theo `code` và `kind`, không phân tích chuỗi thông điệp.
- Response lỗi luôn có `request_id` để tra log.
- Lỗi 500 được xử lý trong middleware thay vì exception handler của FastAPI. Lý do: handler cho `Exception` chạy ở lớp ngoài cùng, sau khi ngữ cảnh request đã kết thúc, nên không còn `request_id`.

## Phương án đã cân nhắc

- **Dùng `HTTPException` trong service:** bị loại. Service sẽ phụ thuộc HTTP.
