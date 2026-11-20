# Tiến độ nâng cấp AI

> Cập nhật sau mỗi milestone. Phiên làm việc tiếp theo đọc file này trước, sau đó đọc [roadmap.md](roadmap.md).

## Trạng thái

| Milestone | Trạng thái | Ngày | Commit |
| --- | --- | --- | --- |
| M1 – Audit & Architecture | Hoàn thành | 2026-11-20 | `docs: audit AI system and plan upgrade` |
| M2 – Context Engine | Chưa bắt đầu | | |
| M3 – Memory Engine | Chưa bắt đầu | | |
| M4 – Tool Registry & Orchestration | Chưa bắt đầu | | |
| M5 – Multi-step Planning | Chờ quyết định D5 | | |
| M6 – Personal Data Retrieval | Chưa bắt đầu | | |
| M7 – RAG & Knowledge | Chờ quyết định D2, D3 | | |
| M8 – Proactive Assistance | Chờ quyết định D5, D6 | | |
| M9 – Chat UX | Chưa bắt đầu | | |
| M10 – Provider Management | Chưa bắt đầu | | |
| M11 – Security & Observability | Chưa bắt đầu | | |
| M12 – Testing & Optimization | Chưa bắt đầu | | |
| M13 – Final Integration | Chưa bắt đầu | | |

## M1 – Audit & Architecture

Phạm vi: chỉ tài liệu. Không đổi code, schema hoặc API.

Đã làm:
- [audit.md](audit.md): hiện trạng, chức năng chưa có logic, vấn đề kiến trúc, bảo mật, UX, hiệu năng, xung đột với CLAUDE.md.
- [architecture.md](architecture.md): kiến trúc đích, ghi rõ phần nào đã có và phần nào là đề xuất.
- [roadmap.md](roadmap.md): milestone, nghiệm thu, 7 quyết định cần người dùng phê duyệt (D1–D7).
- Sửa tài liệu lệch code: `docs/architecture/ai-architecture.md` (registry không rỗng, Memory chưa có đường ghi, tên thành phần thực tế) và `docs/architecture/backend-architecture.md` (danh sách module đã có).

Kết quả cổng chất lượng (chạy trước khi đổi tài liệu, code không đổi sau đó):
- Backend: `pytest` 434 passed; `ruff check`, `mypy app tests`, `alembic check` đạt.
- Frontend: `npm run test` 33 file, 223 test passed.

Vấn đề còn tồn tại: toàn bộ danh sách trong [audit.md](audit.md). Ưu tiên cao nhất: intent không có ngữ cảnh (M2), Memory không có đường ghi (M3), race khi xác nhận đề xuất (M4).

Việc tiếp theo: M2 – Context Engine. Không bị chặn bởi quyết định nào.
