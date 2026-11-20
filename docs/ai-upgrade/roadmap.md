# Lộ trình nâng cấp AI

> Lập ở M1 (2026-11-20), dựa trên [audit.md](audit.md). Thứ tự được sắp theo phụ thuộc và giá trị, không theo số thứ tự của master prompt.
>
> Mỗi milestone kết thúc khi: test mới đạt, toàn bộ cổng chất lượng ở CLAUDE.md mục 23.10 đạt, tài liệu cập nhật, [progress.md](progress.md) cập nhật, có commit.

## Quyết định cần phê duyệt trước khi triển khai

Các milestone đánh dấu 🔒 bị chặn cho tới khi người dùng trả lời.

| ID | Câu hỏi | Đề xuất mặc định | Chặn |
| --- | --- | --- | --- |
| D1 | Authentication: làm ngay hay giữ ADR-0007 (một người dùng, chỉ `127.0.0.1`)? | Giữ ADR-0007 cho tới khi cần truy cập từ thiết bị khác | M11 phần auth |
| D2 | RAG tài liệu: có cần không? Lưu vector ở đâu? | Có, nhưng ở mức tối thiểu: embedding qua Ollama `/api/embed`, vector lưu trong SQLite, tính cosine trong Python. Không thêm vector DB | M7 |
| D3 | Định dạng tài liệu cần hỗ trợ? | `.txt`, `.md` trước (không dependency). PDF cần `pypdf` — thêm khi được duyệt | M7 |
| D4 | Có thêm provider đám mây (OpenAI-compatible) không? | Có adapter, nhưng tắt mặc định; không tự chuyển khi Ollama lỗi | M10 |
| D5 | Có tạo module `tasks` (task, dự án, tiến độ) không? | Có, vì Planning (M5) và Proactive (M8) cần nơi lưu kế hoạch | M5, M8 |
| D6 | Có chạy tác vụ nền (nhắc việc, tóm tắt định kỳ) không? | Hoãn; M8 chỉ làm gợi ý khi người dùng mở ứng dụng | M8 phần scheduler |
| D7 | Streaming qua SSE (endpoint mới, giữ `POST /chat`)? | Có | M10 phần streaming |

## Milestone

### M1 – Audit & Architecture ✅

- Phạm vi: audit, kiến trúc đích, lộ trình, sửa tài liệu lệch code.
- Không đổi code.

### M2 – Context Engine (không bị chặn)

Phạm vi:
- Intent classifier nhận 2–3 lượt gần nhất (đã rút gọn) để hiểu câu tiếp nối.
- Ngân sách ngữ cảnh theo ký tự (`AI_CONTEXT_MAX_CHARS`), áp dụng sau giới hạn số tin nhắn.
- Rút gọn nội dung message `role=tool` cũ (giữ lượt hiện tại đầy đủ).
- Không đổi API.

Nghiệm thu:
- Test: "Báo cáo tháng này" → "Còn tháng trước?" vẫn chọn domain `finance`.
- Test: lịch sử vượt ngân sách bị cắt từ cũ nhất, không cắt giữa cặp tool_call/tool_result.
- Biến cấu hình mới có trong `Settings`, `.env.example`, `backend-architecture.md`, `test_config.py`.

### M3 – Memory Engine (một phần cần duyệt schema)

Phạm vi:
- Migration thêm cột cho `memories` (xem architecture.md mục 4), không mất dữ liệu.
- `MemoryService`: tạo, sửa, xóa, tìm kiếm, chống trùng.
- API `GET/POST/PATCH/DELETE /api/v1/memories`.
- Tool `memory_search` (read), `memory_save`, `memory_forget` (write, cần xác nhận).
- Trang "Ghi nhớ" (đổi catalog sang `available`).

Nghiệm thu: test capture qua xác nhận, chống trùng, cập nhật, xóa, không trả Memory của người dùng khác, không trả Memory không liên quan; một lượt chat dùng `memory_save` qua `MockLLMProvider`.

### M4 – Tool Registry & Orchestration

Phạm vi: metadata `ToolSpec`, timeout riêng từng Tool (sửa lỗi Overpass), bảng `ai_tool_executions`, chống thực thi hai lần khi xác nhận, đề xuất hết hạn, intent nhiều domain (tối đa 2), chạy song song Tool đọc idempotent.

### M9 – Chat UX (một phần làm sớm)

Phạm vi sớm (sau M2): `ConversationMessage` trả thêm danh sách Tool đã dùng; frontend khôi phục chip khi mở lại hội thoại. Tìm kiếm hội thoại. Bảng trong Markdown.
Phạm vi sau (cần D7): streaming, hiển thị bước đang chạy, dừng thật ở backend.

### M10 – Provider Management

Capability của model, token usage từ Ollama (`prompt_eval_count`, `eval_count`), model riêng cho intent, streaming (D7), adapter OpenAI-compatible (D4).

### M11 – Security & Observability

Đánh dấu kết quả Tool là dữ liệu (chống prompt injection), rate limit `/chat`, test bảo mật (cross-user, bỏ qua xác nhận, injection trong kết quả Tool), Debug panel cho owner dựa trên `ai_tool_executions`. Authentication theo D1.

### M5 – Multi-step Planning 🔒 D5

Plan/Step có trạng thái, lưu trong module `tasks`; chế độ direct / planned / interactive / approval; dừng, hủy, tiếp tục; giới hạn số bước và thời gian.

### M6 – Personal Data Retrieval

Tool tìm kiếm liên phân hệ qua `public.py` của từng module (không SQL do LLM tạo); kết quả có `source` (module, id, link) để giao diện mở bản ghi gốc.

### M7 – RAG & Knowledge 🔒 D2, D3

Upload → kiểm tra → trích xuất → chunk → embed → lưu → truy xuất (keyword + vector) → trích dẫn.

### M8 – Proactive Assistance 🔒 D5, D6

Gợi ý theo luật (ngân sách sắp vượt, chuyến đi sắp tới, task quá hạn), bật/tắt, giới hạn tần suất.

### M12 – Testing & Optimization, M13 – Final Integration

Test end-to-end các luồng ở master prompt mục 17.6 với `MockLLMProvider`; đo độ trễ với Ollama thật (thủ công); cập nhật toàn bộ tài liệu.

## Thứ tự đề xuất

```text
M1 → M2 → M9 (sớm) → M3 → M4 → M11 (phần không cần D1) → M10 → M6
     → [chờ D5] M5 → M8
     → [chờ D2/D3] M7
     → M12 → M13
```
