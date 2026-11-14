# ADR-0001: Modular Monolith với ranh giới module qua `public.py`

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

Ứng dụng phục vụ một người dùng, chạy cục bộ, gồm nhiều nhóm nghiệp vụ (AI, Memory, Finance, Travel, Food, Dashboard). CLAUDE.md yêu cầu Modular Monolith và cấm Microservices.

## Quyết định

- Một tiến trình Backend, một database.
- Code tổ chức theo module nghiệp vụ trong `backend/app/modules/`.
- Module khác chỉ được import `app.modules.<module>.public`.
- Quy tắc được kiểm tra tự động bởi `tests/architecture/test_module_boundaries.py`.

## Hệ quả

- Triển khai và debug đơn giản: một tiến trình, một log.
- Ranh giới module không dựa vào kỷ luật cá nhân; vi phạm làm test thất bại.
- Giao tiếp giữa module là lời gọi hàm trong cùng tiến trình. Tách module thành dịch vụ riêng về sau cần thay các lời gọi này.

## Phương án đã cân nhắc

- **Microservices:** bị loại. Chi phí vận hành không tương xứng với quy mô.
- **Phân tầng toàn cục** (`routers/`, `services/`, `models/` chung): bị loại. Nghiệp vụ của một module bị rải ra nhiều thư mục, ranh giới không kiểm tra được.
