# ADR-0008: Logging có cấu trúc bằng thư viện chuẩn

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

CLAUDE.md mục 10 yêu cầu log có cấu trúc, có timestamp, level, module, operation và Request ID.

## Quyết định

- Dùng module `logging` của Python. Không thêm thư viện log.
- `app/core/logging.py` cung cấp `JsonFormatter` (mỗi dòng một object JSON) và `ConsoleFormatter` (dễ đọc khi phát triển). `LOG_FORMAT` chọn formatter.
- Request ID lưu trong `contextvars` và được gắn vào mọi bản ghi bởi `RequestIdFilter`.
- Ngữ cảnh bổ sung truyền qua tham số `extra` của logger.
- `RequestContextMiddleware` ghi access log; access log của uvicorn bị tắt.

## Hệ quả

- Không có dependency mới. Mọi thư viện dùng `logging` tự động đi qua cùng một handler.
- Tìm toàn bộ log của một request bằng một giá trị `request_id`.
- Logger của `aiosqlite`, `asyncio`, `httpcore`, `httpx` bị giới hạn ở mức INFO để log DEBUG của ứng dụng đọc được.

## Phương án đã cân nhắc

- **structlog / loguru:** bị loại. Nhu cầu hiện tại được đáp ứng bằng khoảng 100 dòng code trên thư viện chuẩn.
