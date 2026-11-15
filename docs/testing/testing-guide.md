# Hướng dẫn kiểm thử

Chiến lược kiểm thử: [development-workflow.md](../architecture/development-workflow.md) mục 4.

## Nguyên tắc

- Test không cần Ollama, không cần mạng, không đọc `.env` của người phát triển.
- Mỗi test Backend có một database SQLite riêng, tạo bằng migration thật.
- Test AI kiểm tra hành vi (Tool nào chạy, tham số nào, dữ liệu nào được lưu), không so sánh nguyên văn câu trả lời.
- Không sửa hoặc xóa test chỉ để test đạt.

## Backend

Chạy trong `backend/`.

| Mục đích | Lệnh |
| --- | --- |
| Toàn bộ test | `uv run pytest` |
| Một thư mục | `uv run pytest tests/modules/ai` |
| Một file | `uv run pytest tests/modules/ai/test_orchestrator.py` |
| Một test | `uv run pytest tests/modules/ai/test_orchestrator.py::test_tool_loop_stops_at_the_iteration_limit` |
| Theo tên | `uv run pytest -k "migration"` |
| Dừng ở lỗi đầu tiên, in chi tiết | `uv run pytest -x -vv` |
| Xem log của test thất bại | Mặc định Pytest in log đã bắt được |
| Test chậm nhất | `uv run pytest --durations=10` |
| Lint | `uv run ruff check .` |
| Kiểm tra định dạng | `uv run ruff format --check .` |
| Type check | `uv run mypy app tests` |

### Tổ chức test

| Thư mục | Nội dung | Loại |
| --- | --- | --- |
| `tests/architecture/` | Quy tắc import giữa các module | Architecture |
| `tests/core/` | Cấu hình, logging, Request ID, CORS, error envelope | Unit, API |
| `tests/infrastructure/` | Kết nối database, migration | Infrastructure |
| `tests/modules/health/` | Health check, khởi động khi không có Ollama | API |
| `tests/modules/memory/` | Ràng buộc database, repository, service, truy xuất Memory | Repository, Service |
| `tests/modules/ai/` | Registry, Executor, Intent, Context, Provider, Orchestrator, Chat API | Unit, Service, API |

### Fixture dùng chung (`tests/conftest.py`)

| Fixture | Cung cấp |
| --- | --- |
| `database_path` | File SQLite riêng của test, đã migrate tới `head` |
| `settings` | `Settings` cho môi trường `testing`, `LLM_PROVIDER=mock` |
| `app` | Ứng dụng FastAPI đã khởi động |
| `client` | `httpx.AsyncClient` gọi thẳng vào `app` |
| `session` | `AsyncSession` trên database của test |

### Kiểm thử AI

`tests/ai_support.py` cung cấp:

- `MockLLMProvider(script)`: mỗi phần tử của `script` là một câu trả lời (chuỗi), một danh sách tool call, hoặc một exception. Provider ghi lại mọi lời gọi trong `calls`.
- Tool mẫu: `EchoTool` (thành công), `BusinessFailureTool` (lỗi nghiệp vụ), `CrashingTool` (lỗi bất ngờ), `SlowTool` (quá thời gian), `BadOutputTool` (kết quả sai contract).
- `build_runtime(provider, tools)`: lắp `AIRuntime` cho test.

Ví dụ kịch bản một lượt chat có dùng Tool:

```python
provider = MockLLMProvider([
    '{"intent": "demo"}',                    # phân loại ý định
    [tool_call("demo_echo", text="a")],      # model yêu cầu Tool
    "Kết quả là a",                          # model trả lời
])
```

Để test endpoint chat với kịch bản riêng, gán `app.state.ai_runtime` trước khi ứng dụng khởi động (xem `tests/modules/ai/test_chat_api.py`).

### Kiểm thử migration

`tests/infrastructure/test_migrations.py` kiểm tra: `upgrade head` trên database trống; `downgrade base`; `upgrade` lại; và model khớp schema sau migration. Test cuối thất bại khi model thay đổi mà thiếu migration.

## Frontend

Chạy trong `frontend/`.

| Mục đích | Lệnh |
| --- | --- |
| Toàn bộ test | `npm run test` |
| Chế độ theo dõi | `npm run test:watch` |
| Một file | `npx vitest run src/hooks/useAsyncData.test.ts` |
| Theo tên | `npx vitest run -t "retries"` |
| Lint | `npm run lint` |
| Type check và build | `npm run build` |

File test đặt cạnh file nguồn (`X.tsx` và `X.test.tsx`).

| Loại | Ví dụ |
| --- | --- |
| Component | `SystemStatusPanel.test.tsx`, `ModuleNotes.test.tsx`, `ChatPanel.test.tsx`, `ErrorBoundary.test.tsx`, `ui.test.tsx` |
| Hook | `useAsyncData.test.ts` |
| API service | `errors.test.ts`, `client.test.ts`, `features/system-status/api.test.ts` |
| Routing | `app/router.test.tsx` |
| Cấu hình | `config/env.test.ts` |

Test không gọi Backend thật. Component test thay module `api.ts` của feature bằng `vi.mock`. Test của API client truyền `adapter` giả vào `createApiClient`.

## Kiểm thử thủ công

Các nội dung sau chưa có test tự động:

| Nội dung | Cách kiểm tra |
| --- | --- |
| Giao diện trong trình duyệt | Chạy Backend và Frontend, mở `http://localhost:5710` |
| Chat với Ollama thật | Đặt `OLLAMA_MODEL`, gửi `POST /api/v1/chat` qua `http://127.0.0.1:8710/docs` |
| Tool calling với model thật | Cần có Tool nghiệp vụ đầu tiên |

## Trước khi báo hoàn thành

```bash
# backend/
uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy app tests && uv run alembic check

# frontend/
npm run test && npm run lint && npm run build
```
