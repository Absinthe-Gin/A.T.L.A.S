# Hướng dẫn debug

## Quy trình

1. Tái hiện lỗi.
2. Lấy `request_id` từ response lỗi (`error.request_id`) hoặc header `X-Request-ID`.
3. Tìm mọi dòng log có `request_id` đó.
4. Xác định module và tầng từ tên logger và từ `error.code`.
5. Phân tích nguyên nhân gốc.
6. Viết test tái hiện lỗi. Test phải thất bại trước khi sửa.
7. Sửa, rồi chạy test liên quan và toàn bộ test.

## Đọc log Backend

Log ghi ra stderr của tiến trình uvicorn.

Định dạng `LOG_FORMAT=console`:

```text
2026-11-14 23:07:03,338 INFO     [9a0f8d73969a448b] app.modules.ai.execution.log_turn: Chat turn completed | intent='general' provider='mock' status='success'
```

Thứ tự: thời gian, mức log, `[request_id]`, `logger.hàm`, thông điệp, rồi các trường ngữ cảnh sau dấu `|`.

Định dạng `LOG_FORMAT=json`: mỗi dòng một object JSON với các trường `timestamp`, `level`, `logger`, `function`, `message`, `request_id`, cùng các trường ngữ cảnh.

Tên logger cho biết vị trí:

| Logger | Vị trí |
| --- | --- |
| `app.core.middleware` | Access log và lỗi chưa lường trước |
| `app.core.error_handlers` | Lỗi được chuyển thành response |
| `app.modules.<module>.service` | Tầng nghiệp vụ |
| `app.modules.<module>.repository` | Tầng dữ liệu |
| `app.modules.ai.providers.ollama` | Giao tiếp với Ollama |
| `app.modules.ai.tools.executor` | Thực thi Tool |
| `app.modules.ai.execution` | Nhật ký thực thi AI |

`LOG_LEVEL=DEBUG` bật log chi tiết của ứng dụng. Logger của `aiosqlite`, `asyncio`, `httpcore`, `httpx` luôn ở mức INFO.

## Tra lỗi theo mã

| `error.code` | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| `internal_server_error` | Exception chưa lường trước | Tìm dòng `Unhandled exception` cùng `request_id`; stack trace nằm ngay sau |
| `default_user_missing` | Database chưa migrate | `uv run alembic upgrade head` |
| `validation_error` | Request sai | Xem `error.details` |
| `conversation_not_found` | Sai `conversation_id` | Kiểm tra ID; hội thoại của người dùng khác cũng trả mã này |
| `llm_not_configured` | `OLLAMA_MODEL` rỗng | Đặt giá trị trong `backend/.env`, khởi động lại |
| `llm_unavailable` | Ollama không chạy hoặc sai `OLLAMA_BASE_URL` | Chạy `ollama serve`; kiểm tra `GET /api/v1/health` |
| `llm_timeout` | Model phản hồi chậm | Tăng `LLM_TIMEOUT_SECONDS` hoặc dùng model nhỏ hơn |
| `llm_request_failed` | Ollama trả HTTP lỗi, thường do model chưa được tải | `ollama pull <model>`; xem `status_code` trong log |
| `llm_invalid_response` | Ollama trả dữ liệu sai cấu trúc | Xem log của `app.modules.ai.providers.ollama` |

## Debug một lượt chat

Một lượt chat sinh các dòng log sau, cùng `request_id`:

| Thông điệp | Trường quan trọng |
| --- | --- |
| `Tool executed` | `tool_name`, `tool_input` (đã che dữ liệu nhạy cảm), `status`, `error_code`, `duration_ms` |
| `Chat turn completed` | `conversation_id`, `message_id`, `intent`, `provider`, `model`, `iterations`, `tools`, `status`, `duration_ms` |
| `Request completed` | `status_code`, `duration_ms` |

Giá trị `status` của `Chat turn completed`:

| `status` | Ý nghĩa |
| --- | --- |
| `success` | Model trả lời bình thường |
| `clarification` | Intent là `unknown`; trợ lý hỏi lại người dùng |
| `tool_limit_reached` | Vượt `AI_MAX_TOOL_ITERATIONS` |
| `empty_reply` | Model trả nội dung rỗng |

Mã lỗi của Tool (`error_code` trong `Tool executed`):

| Mã | Ý nghĩa |
| --- | --- |
| `tool_not_found` | Model gọi Tool không tồn tại hoặc không thuộc intent hiện tại |
| `invalid_tool_input` | Tham số do model tạo không qua được validation |
| `tool_timeout` | Tool chạy quá `AI_TOOL_TIMEOUT_SECONDS` |
| `tool_execution_failed` | Tool ném exception bất ngờ; có dòng `Tool raised an unexpected error` kèm stack trace |
| `invalid_tool_output` | Tool trả kết quả sai `output_model`; đây là lỗi lập trình |
| Mã khác | Mã lỗi nghiệp vụ do service của module ném ra |

Lịch sử đầy đủ của hội thoại nằm trong bảng `messages`:

```sql
SELECT sequence, role, tool_name, content, metadata
FROM messages
WHERE conversation_id = '<id không có dấu gạch ngang>'
ORDER BY sequence;
```

- Message `assistant` có `metadata.tool_calls`: model đã yêu cầu Tool.
- Message `tool`: kết quả thực thi, với `metadata.status`, `metadata.error_code`, `metadata.duration_ms`.
- Message `assistant` cuối lượt: `metadata.intent`, `metadata.model`, `metadata.iterations`, `metadata.status`.

SQLite lưu UUID dạng 32 ký tự hex, không có dấu gạch ngang.

## Debug database

| Mục đích | Lệnh (trong `backend/`) |
| --- | --- |
| Revision hiện tại | `uv run alembic current` |
| Model có khớp migration không | `uv run alembic check` |
| Lịch sử migration | `uv run alembic history` |

File database phát triển: `backend/data/app.db`. Mở bằng công cụ SQLite bất kỳ.

Lỗi `MissingGreenlet`: code truy cập một thuộc tính ORM chưa được nạp, khiến SQLAlchemy thử truy vấn đồng bộ. Nạp dữ liệu tường minh bằng `selectinload`, hoặc đọc giá trị trước khi session hết hiệu lực.

Lỗi `InvalidRequestError ... lazy='raise'`: code truy cập một quan hệ chưa được nạp. Thêm `selectinload` vào truy vấn.

## Debug Frontend

- Mọi lỗi API là một `ApiError` (`src/services/api/errors.ts`) với `kind`, `status`, `code`, `message`, `details`, `requestId`.
- `requestId` được hiển thị cùng thông báo lỗi. Dùng nó để tìm log Backend.
- Lỗi render được ghi qua `reportError` với tiền tố `[app-error]` trong console của trình duyệt.

| Hiện tượng | Nguyên nhân thường gặp |
| --- | --- |
| Thông báo "Không kết nối được tới máy chủ" | Backend chưa chạy, hoặc sai `VITE_API_BASE_URL` |
| Lỗi CORS trong console | Origin của Frontend không có trong `CORS_ALLOWED_ORIGINS` |
| `npm run dev` báo `Port 5710 is already in use` | Cổng đang bị chiếm. Dev server không tự đổi cổng vì Backend chỉ cho phép origin đã cấu hình |
| Lỗi `Missing VITE_API_BASE_URL` khi khởi động | Chưa tạo `frontend/.env` |
| Sửa `.env` không có tác dụng | Cần khởi động lại `npm run dev` |

## Lỗi môi trường đã biết

### Vitest báo "failed to find the current suite"

Terminal đang đứng ở đường dẫn có ký tự ổ đĩa viết thường (`c:\...`). Chuyển vào thư mục bằng ký tự viết hoa (`cd C:\...\frontend`) rồi chạy lại.

### Chữ tiếng Việt trong log bị thay bằng `\u1ea5...`

Xảy ra trên Windows khi chuyển hướng log vào file. Đặt biến môi trường `PYTHONUTF8=1` trước khi chạy server.

### Repository nằm trong thư mục đồng bộ

OneDrive và công cụ tương tự đồng bộ cả `.venv/`, `node_modules/` và file SQLite. Hệ quả có thể gặp: cài dependency chậm, lỗi khóa file, lỗi `database is locked`, file database hỏng.

Cách xử lý: chuyển repository ra thư mục không đồng bộ, hoặc loại trừ `backend/.venv`, `backend/data`, `frontend/node_modules` khỏi đồng bộ.

### Cổng đang bị chiếm

Backend dùng cổng 8710, Frontend dùng 5710. Tìm tiến trình đang giữ cổng trên Windows:

```powershell
netstat -ano | findstr :8710
```
