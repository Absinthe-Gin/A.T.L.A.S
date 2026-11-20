# Audit hệ thống AI hiện tại

> Ngày audit: 2026-11-20. Commit: `1da029c`. Phạm vi: toàn bộ AI Core, Personal Memory, Tool, giao diện Chat và các phần liên quan.
>
> Tài liệu này mô tả **hiện trạng thực tế** của code. Mọi nhận định đều dẫn tới file cụ thể. Kế hoạch nâng cấp nằm ở [roadmap.md](roadmap.md), thiết kế đích ở [architecture.md](architecture.md).

## 0. Kết quả cổng chất lượng tại thời điểm audit

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest` | 434 passed |
| `uv run ruff check .` | Đạt |
| `uv run mypy app tests` | Đạt (135 file) |
| `uv run alembic check` | Không có thay đổi schema chưa có migration |
| `npm run test` | 33 file, 223 test passed |

Hệ thống hiện tại ổn định. Mọi nâng cấp phải giữ các cổng này ở trạng thái đạt.

## 1. Chức năng hiện có

### 1.1. Backend — AI Core (`backend/app/modules/ai/`)

| Thành phần | File | Mô tả ngắn |
| --- | --- | --- |
| Orchestrator | `orchestrator.py` | Một lượt chat: lưu tin nhắn, nạp lịch sử, phân loại intent, vòng lặp Tool, lưu trả lời, ghi log |
| Context builder | `context.py` | Ghép system prompt + Memory liên quan + N tin nhắn gần nhất + tin nhắn mới |
| Intent classifier | `intent.py` | Gọi LLM với JSON schema, trả về một domain, `general` hoặc `unknown` |
| Prompt | `prompts.py` | System prompt tiếng Việt, prompt phân loại, câu trả lời dự phòng |
| Tool registry | `tools/registry.py` | Đăng ký Tool, kiểm tra tên `<domain>_<action>`, lọc theo domain |
| Tool executor | `tools/executor.py` | Validate input/output bằng Pydantic, timeout, chuẩn hóa lỗi thành `ToolResult`, tách Tool ghi thành đề xuất |
| Pending actions | `actions.py`, `models.py` | Bảng `ai_pending_actions`; xác nhận/hủy một lần; kết quả được ghi lại vào hội thoại dưới dạng message `system` |
| Execution log | `execution_log.py` | Log có cấu trúc cho từng Tool và từng lượt; `redact()` che khóa nhạy cảm |
| LLM provider | `providers/base.py`, `ollama.py`, `mock.py`, `factory.py` | Interface trung lập; adapter Ollama (`/api/chat`, `stream: false`); provider giả cho test |
| API | `router.py` | `POST /chat`, `GET /chat/conversations/{id}/actions`, `POST /chat/actions/{id}/confirm`, `POST /chat/actions/{id}/cancel` |

### 1.2. Backend — Personal Memory (`backend/app/modules/memory/`)

- Bảng `conversations`, `messages`, `memories`.
- `ConversationService`: tạo, đọc, đổi tên, xóa hội thoại; thêm tin nhắn; phân trang tin nhắn hiển thị.
- `MemoryService.find_relevant()`: chấm điểm theo số từ khóa trùng, trên 200 Memory mới nhất.
- API: `GET/PATCH/DELETE /conversations...`, `GET /conversations/{id}/messages`.

### 1.3. Tool nghiệp vụ đã đăng ký (`app/bootstrap.py`)

| Tool | Domain | Effect |
| --- | --- | --- |
| `finance_get_monthly_report` | finance | read |
| `finance_list_transactions` | finance | read |
| `finance_list_categories` | finance | read |
| `finance_create_transaction` | finance | write (cần xác nhận) |
| `travel_search_places` | travel | read |
| `travel_get_weather` | travel | read |
| `travel_find_transport` | travel | read |
| `travel_list_plans` | travel | read |
| `travel_create_plan` | travel | write (cần xác nhận) |
| `food_recommend_dishes` | food | read |
| `food_find_restaurants` | food | read |

Tổng: 11 Tool, 3 domain, 2 Tool ghi.

### 1.4. Frontend — Chat (`frontend/src/features/chat/`, `pages/ChatPage.tsx`)

- Sidebar lịch sử hội thoại nhóm theo thời gian, đổi tên, xóa, thu gọn (desktop), drawer (mobile).
- Composer: nhiều dòng, Enter gửi, Shift+Enter xuống dòng, xử lý IME tiếng Việt, đếm ký tự, nút dừng chờ.
- Tin nhắn: Markdown tự viết (`markdown.ts`: đoạn, tiêu đề, danh sách, code, link đã lọc scheme), sao chép, gửi lại khi lỗi.
- Thẻ đề xuất (`PendingActionCard.tsx`) với Xác nhận/Hủy; ghi chú `system` hiển thị kết quả.
- Chip "Đã dùng <phân hệ>" theo Tool đã gọi trong lượt (chỉ khi đang xem trực tiếp).
- Cảnh báo khi Ollama chưa sẵn sàng (qua `/health`).

## 2. Chức năng đang hoạt động (đã có test tự động)

- Luồng chat không Tool, một Tool, nhiều vòng Tool, Tool sai tên, tham số sai, vượt giới hạn vòng lặp, provider lỗi (`tests/modules/ai/test_orchestrator.py`).
- Tool ghi luôn thành đề xuất; xác nhận chạy lại validation; xác nhận lặp lại trả 409 (`test_pending_actions.py`).
- Không trộn tin nhắn giữa các hội thoại; giới hạn N tin nhắn (`test_intent_and_context.py`).
- Adapter Ollama với `httpx.MockTransport`: timeout, mất kết nối, JSON sai (`test_providers.py`).
- Ranh giới module được kiểm tra tự động (`tests/architecture/test_module_boundaries.py`).

Lưu ý: tài liệu `ai-architecture.md` ghi "Chưa kiểm thử với Ollama thật". Audit này không chạy Ollama thật.

## 3. Chức năng chỉ có giao diện hoặc chỉ có schema, chưa có logic

| Hạng mục | Hiện trạng | Bằng chứng |
| --- | --- | --- |
| Long-term Memory | Có bảng `memories` và hàm đọc, nhưng **không có đường ghi nào**: không API, không Tool, không service tạo Memory. Thực tế bảng luôn rỗng, nên bước Memory Retrieval không bao giờ có dữ liệu | `memory/service.py` chỉ có `find_relevant`; `grep` không thấy nơi tạo `Memory(...)` ngoài test |
| Trang "Ghi nhớ" | Khai báo `status: 'planned'` trong catalog; chưa có trang | `frontend/src/features/modules/catalog.tsx` |
| `MemoryCategory`, `MemorySource.AI_INFERRED` | Có enum, chưa có luồng nào tạo ra | `memory/models.py` |
| Chi tiết xử lý của tin nhắn cũ | Khi mở lại hội thoại, chip Tool và intent bị mất (`intent: 'general'`, `toolCalls: []`) dù backend đã lưu trong `messages.metadata` | `frontend/src/features/chat/history.ts` |

## 4. Chức năng chưa hoàn thiện

### 4.1. Context

- **Intent classifier chỉ nhận tin nhắn hiện tại**, không nhận lịch sử (`intent.py`, `orchestrator.py`: `classify(text, ...)`). Câu tiếp nối như "Trong 30 ngày" hoặc "Còn tháng trước thì sao?" dễ bị phân loại `unknown` (hỏi lại) hoặc `general` (không có Tool). Đây là lỗi hành vi quan trọng nhất của Context Engine.
- Một lượt chỉ dùng **một domain**. Yêu cầu liên phân hệ ("chuyến đi Đà Nẵng tháng sau tốn bao nhiêu so với ngân sách") không thể dùng Tool của hai domain.
- Cửa sổ ngữ cảnh tính theo **số tin nhắn** (`AI_CONTEXT_MAX_MESSAGES=20`), không theo token. Message `role=tool` (JSON kết quả tìm địa điểm, giao dịch) chiếm chỗ trong cửa sổ và có thể rất dài.
- Không có trạng thái yêu cầu đang xây dựng (slot/working state). Việc duy trì yêu cầu nhiều lượt phụ thuộc hoàn toàn vào LLM đọc lại lịch sử.
- Không có ngữ cảnh ứng dụng (trang hiện tại, bản ghi đang xem). `ChatRequest` chỉ có `message` và `conversation_id`.
- Không có tóm tắt hội thoại dài; tin nhắn ngoài cửa sổ bị bỏ hoàn toàn.

### 4.2. Memory

- Truy xuất bằng trùng từ khóa đơn giản; không xử lý biến thể từ tiếng Việt, không có ngưỡng, không có thời hạn.
- Thiếu: loại Memory theo vòng đời (short-term, episodic), độ tin cậy, trạng thái (active/archived), thời hạn, chống trùng lặp, cập nhật, xóa, UI quản lý.

### 4.3. Tool system

- `ToolSpec` chỉ có `name`, `description`, `domain`, `effect`, `input_model`, `output_model`. Chưa có category, timeout riêng, retry policy, idempotency, audit policy.
- Timeout chung cho mọi Tool (`AI_TOOL_TIMEOUT_SECONDS=15`), trong khi Overpass được cấu hình 30 giây ở adapter (xem mục 8).
- Không có retry có kiểm soát; LLM tự thử lại trong giới hạn vòng lặp.
- Lịch sử thực thi Tool chỉ nằm trong `messages` (role `tool`) và log. Không có bảng thực thi riêng để tra cứu, thống kê.
- Tool chạy tuần tự; chưa có thực thi song song cho Tool đọc.
- Đề xuất (`ai_pending_actions`) không có thời hạn hết hiệu lực.

### 4.4. Planning / multi-step

- Chỉ có vòng lặp Tool (tối đa 5 lần gọi model). Không có khái niệm Plan, Step, trạng thái thực thi, pause/resume.
- Hệ thống chưa có module Task/Project/Note để lưu kế hoạch hoặc theo dõi tiến độ.

### 4.5. Personal Data Retrieval và RAG

- Truy xuất dữ liệu chỉ qua các Tool đọc theo từng domain. Không có tìm kiếm chung liên phân hệ.
- Không có upload tài liệu, trích xuất, chunking, embedding, chỉ mục, trích dẫn nguồn.
- Không có Tool trả về tham chiếu bản ghi để giao diện mở bản ghi gốc.

### 4.6. Provider

- Chỉ có Ollama và Mock. Không có khai báo capability (tool calling, streaming, embedding, context window).
- Không có streaming; người dùng chờ toàn bộ câu trả lời (frontend timeout 90 giây).
- Không đo token usage (Ollama có trả `prompt_eval_count`, `eval_count` nhưng adapter bỏ qua).
- Không chọn model theo tác vụ; intent và trả lời dùng chung một model.

### 4.7. Chat UX

- Chưa có: tìm kiếm hội thoại, ghim, lưu trữ, sửa tin nhắn đã gửi, tạo lại câu trả lời, đính kèm tệp, bảng trong Markdown, xuất hội thoại.
- "Dừng" chỉ ngừng chờ ở phía trình duyệt; backend vẫn chạy hết lượt và lưu câu trả lời. Khi tải lại hội thoại, câu trả lời "đã dừng" vẫn xuất hiện.

## 5. Vấn đề kiến trúc

| # | Vấn đề | Ảnh hưởng | Đề xuất |
| --- | --- | --- | --- |
| A1 | `ai-architecture.md` lệch với code: ghi "Registry rỗng khi chạy thật", "Memory được lưu qua Tool của module memory", nhắc `MemoryRetriever`, `ConversationContextBuilder` không tồn tại | Người phát triển hiểu sai hệ thống | Đã sửa trong M1 |
| A2 | `backend-architecture.md` ghi chỉ có `health`, `users`, `memory`, `ai` | Như trên | Đã sửa trong M1 |
| A3 | Orchestrator gánh nhiều việc: quản lý hội thoại, phân loại, vòng lặp, đề xuất, log | Khó mở rộng khi thêm context selection, planning, streaming | Tách `ContextEngine` (M2) và `TurnRunner`/planner (M5) dần, không viết lại |
| A4 | `PendingActionService` và repository nằm chung trong `actions.py` (172 dòng), model ở `models.py` | Chấp nhận được hiện tại | Tách khi `actions.py` vượt ~300 dòng |
| A5 | Intent là một domain duy nhất, đồng thời là bộ lọc Tool | Chặn yêu cầu liên phân hệ | M4: intent trả danh sách domain, có giới hạn số Tool |
| A6 | Mỗi lượt có 2+ lần gọi LLM (intent + trả lời) | Độ trễ cao với model cục bộ | M2/M10: cho phép bỏ bước intent khi số Tool nhỏ, hoặc dùng model nhỏ hơn cho intent |

## 6. Vấn đề bảo mật

| # | Vấn đề | Mức | Ghi chú |
| --- | --- | --- | --- |
| S1 | Không có authentication | Chấp nhận có điều kiện | ADR-0007; backend chỉ lắng nghe `127.0.0.1`. Phải giải quyết **trước** khi mở ra mạng LAN/Internet |
| S2 | Xác nhận đề xuất có race condition: hai request `confirm` đồng thời đều đọc `status=pending` rồi cùng thực thi | Trung bình | Cần cập nhật trạng thái có điều kiện (`UPDATE ... WHERE status='pending'`) trước khi thực thi |
| S3 | `append_message` lấy `max(sequence)+1` rồi ghi; hai lượt đồng thời trên cùng hội thoại sẽ vi phạm unique và trả 500 | Thấp (giao diện chặn gửi song song) | Bắt lỗi unique và thử lại, hoặc khóa theo hội thoại |
| S4 | Kết quả Tool (dữ liệu OpenStreetMap, ghi chú người dùng) được đưa thẳng vào ngữ cảnh mà system prompt không nói rõ "đây là dữ liệu, không phải chỉ dẫn" | Trung bình | M11: bao kết quả Tool trong khung dữ liệu và thêm quy tắc chống prompt injection; Tool ghi vẫn luôn cần xác nhận nên rủi ro thay đổi dữ liệu đã được chặn |
| S5 | Không có rate limit cho `/chat` | Thấp (localhost) | Cần khi có nhiều người dùng |
| S6 | `redact()` chỉ che theo tên khóa | Thấp | Không có Tool nào nhận bí mật; giữ nguyên |
| S7 | Đề xuất không hết hạn | Thấp | Xác nhận một đề xuất cũ nhiều ngày vẫn chạy; thêm `expires_at` ở M4 |

Điểm tốt đã có: `user_id` chỉ lấy từ `ToolContext`; Tool ghi không bao giờ chạy theo lời model; tham số được validate lại khi xác nhận; xác nhận ràng buộc với `action_id` + `user_id` + tham số đã lưu; lỗi nội bộ không lộ ra model hoặc frontend; link Markdown lọc scheme.

## 7. Vấn đề UX

- Không có streaming: với model cục bộ, người dùng có thể chờ 10–60 giây chỉ thấy dấu ba chấm.
- Không thấy bước đang chạy (đang tra thời tiết, đang tìm quán).
- Mở lại hội thoại mất thông tin Tool đã dùng.
- Câu hỏi tiếp nối bị hỏi lại do intent thiếu ngữ cảnh (mục 4.1).
- Không có cách xem/xóa những gì trợ lý "nhớ" (vì chưa có Memory thật).

## 8. Vấn đề hiệu năng

- 2 lần gọi LLM tối thiểu mỗi lượt; tối đa 1 + `AI_MAX_TOOL_ITERATIONS`.
- `find_relevant` nạp 200 Memory rồi chấm điểm trong Python. Đủ cho quy mô cá nhân.
- `list_for_user` của hội thoại dùng subquery `max(created_at)` trên toàn bảng `messages` theo nhóm. Chấp nhận được hiện tại; cần index khi dữ liệu lớn.
- Một số adapter ngoài đã có cache trong bộ nhớ (`TtlCache` trong `infrastructure/http/fetch.py`, dùng ở `flights.py`, `geo.py`). Tầng AI không cache thêm; chưa cần.
- `food_find_restaurants` gọi Overpass với timeout 30 giây, nhưng `ToolExecutor` cắt mọi Tool ở 15 giây. Truy vấn Overpass chậm sẽ thành `tool_timeout` trước khi adapter kịp dùng phương án dự phòng.

## 9. Chức năng cần bổ sung (ưu tiên theo giá trị / rủi ro)

1. Intent và Tool selection có ngữ cảnh hội thoại (M2).
2. Ngân sách ngữ cảnh theo ký tự/token và rút gọn kết quả Tool cũ (M2).
3. Memory có đường ghi qua Tool có xác nhận, API CRUD, trang "Ghi nhớ" (M3).
4. Hiển thị lại Tool đã dùng khi mở hội thoại cũ (M9, nhỏ).
5. Bảng thực thi Tool, metadata Tool mở rộng, chống race khi xác nhận (M4, M11).
6. Yêu cầu liên phân hệ (M4).
7. Streaming (M10 + M9).
8. Tìm kiếm dữ liệu cá nhân liên phân hệ (M6).
9. RAG tài liệu (M7) — cần quyết định của người dùng (xem roadmap).
10. Authentication (M11) — cần quyết định của người dùng.

## 10. Chức năng cần refactor

| Mục | Lý do | Phạm vi |
| --- | --- | --- |
| `Orchestrator.handle` | Sẽ nhận thêm context engine, multi-domain, streaming | Tách dần theo milestone, giữ API công khai |
| `IntentClassifier.classify(text, domains)` | Cần nhận lịch sử ngắn | Đổi chữ ký trong M2, cập nhật test |
| `ToolSpec` | Thêm metadata | Thêm trường có giá trị mặc định, không phá Tool hiện có |
| `history.ts` (frontend) | Đọc `meta` để khôi phục chip Tool | Cần backend trả thêm trường trong `ConversationMessage` |

## 11. Những yêu cầu của master prompt xung đột với quy tắc dự án

Các mục sau **không** được triển khai tự động; chúng cần người dùng quyết định vì CLAUDE.md yêu cầu phê duyệt:

| Yêu cầu | Quy tắc liên quan | Cần quyết định |
| --- | --- | --- |
| Authentication bắt buộc (14.1) | ADR-0007 hoãn authentication; mục 3.2 "chưa có authentication" | Có làm authentication ngay không, theo hình thức nào |
| Vector storage, embedding (6.4, 10) | CLAUDE.md mục 7: không dùng Vector Database trong MVP khi chưa xác nhận nhu cầu | Có cần RAG tài liệu không; lưu vector ở SQLite (không thêm dependency) hay dùng extension |
| Upload và trích xuất tài liệu PDF/DOCX | Mục 15: dependency mới cần đánh giá | Định dạng nào cần hỗ trợ |
| Provider OpenAI-compatible | Mục 12.2: không tự chuyển provider làm lộ dữ liệu | Có cho phép gửi dữ liệu ra dịch vụ đám mây không |
| Task/Project/Note (8, 9, 11) | Mục 19: module mới phải có yêu cầu thực tế | Có tạo module `tasks` (hoặc `notes`) không |
| Proactive và scheduled tasks (11) | Mục 3.1: không thêm hạ tầng phức tạp khi chưa cần | Có cần chạy nền (scheduler) không |
| Streaming | Mục 9: đổi API contract | Đồng ý thêm endpoint SSE mới, giữ `POST /chat` |
