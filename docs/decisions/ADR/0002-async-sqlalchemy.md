# ADR-0002: SQLAlchemy 2 ở chế độ async

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

Luồng Chat gọi LLM qua HTTP và có thể kéo dài nhiều giây. FastAPI chạy endpoint async trên một event loop. Một truy vấn database đồng bộ trong endpoint async sẽ chặn mọi request khác.

## Quyết định

- Dùng `AsyncEngine` và `AsyncSession`.
- Driver: `aiosqlite` cho SQLite. Khi chuyển sang PostgreSQL dùng `asyncpg`.
- Session dùng `expire_on_commit=False`.
- Quan hệ ORM khai báo `lazy="raise"`; dữ liệu liên quan phải được nạp tường minh.

## Hệ quả

- Toàn bộ luồng I/O nhất quán async, đúng CLAUDE.md mục 4.1.
- Truy cập thuộc tính chưa nạp gây lỗi ngay, không sinh truy vấn ngầm. Điều này cũng ngăn N+1.
- Thêm dependency `aiosqlite` và `greenlet`.
- Alembic chạy migration qua engine async (`alembic/env.py`).

## Phương án đã cân nhắc

- **Session đồng bộ, endpoint `def`:** bị loại. Orchestrator cần `await` lời gọi LLM, nên phải trộn hai mô hình.
