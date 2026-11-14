# Backend — AI Personal Assistant

FastAPI + SQLAlchemy (async) + Alembic. Kiến trúc Modular Monolith.

Kiến trúc và quy ước: [docs/architecture/backend-architecture.md](../docs/architecture/backend-architecture.md).

## Lệnh

Chạy trong thư mục `backend/`.

| Mục đích | Lệnh |
| --- | --- |
| Cài dependency | `uv sync` |
| Tạo file cấu hình | Sao chép `.env.example` thành `.env` |
| Áp dụng migration | `uv run alembic upgrade head` |
| Chạy server | `uv run python -m app` |
| Chạy test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Định dạng code | `uv run ruff format .` |
| Type check | `uv run mypy app tests` |

## Migration

| Mục đích | Lệnh |
| --- | --- |
| Tạo migration từ thay đổi model | `uv run alembic revision --autogenerate -m "<mô tả>"` |
| Kiểm tra model khớp migration | `uv run alembic check` |
| Xem revision hiện tại | `uv run alembic current` |
| Lùi một revision | `uv run alembic downgrade -1` |

Luôn đọc và chỉnh file migration được sinh ra trước khi áp dụng. `downgrade` có thể xóa dữ liệu.

## Cấu trúc

```text
app/
├── main.py            # create_app()
├── bootstrap.py       # Composition root: lắp ráp AI runtime, đăng ký Tool
├── api/v1.py          # Gom router dưới /api/v1
├── core/              # Cấu hình, logging, middleware, exception
├── shared/            # Tool contract
├── infrastructure/    # Database engine, session, base model
└── modules/
    ├── health/        # GET /api/v1/health
    ├── users/         # Người dùng hiện tại
    ├── memory/        # Hội thoại, tin nhắn, Memory
    └── ai/            # Orchestrator, Tool, LLM Provider, POST /api/v1/chat
```

Module khác chỉ được import `app.modules.<module>.public`. Quy tắc này được kiểm tra bởi `tests/architecture/`.

## Thêm một module nghiệp vụ

1. Tạo `app/modules/<tên>/` với `models.py`, `repository.py`, `service.py`, `schemas.py`, `router.py`, `dependencies.py`, `public.py` theo nhu cầu thực tế.
2. Import `models` của module trong `app/infrastructure/database/models.py`.
3. Tạo migration: `uv run alembic revision --autogenerate -m "..."`.
4. Thêm router vào `app/api/v1.py`.
5. Nếu module cung cấp Tool cho AI: định nghĩa trong `tools.py` và đăng ký tại `build_tool_registry()` trong `app/bootstrap.py`.
6. Viết test trong `tests/modules/<tên>/`.
7. Cập nhật `docs/database/schema.md` và `docs/api/api-reference.md`.
