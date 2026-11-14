# ADR-0010: `uv` quản lý môi trường và dependency Python

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

Backend cần môi trường ảo, khai báo dependency và phiên bản được khóa để cài đặt tái lập được.

## Quyết định

- Dependency khai báo trong `backend/pyproject.toml`. Dev dependency nằm trong nhóm `dev`.
- `backend/uv.lock` được commit.
- Mọi lệnh chạy qua `uv run`; `uv sync` tạo `.venv` và cài đúng phiên bản đã khóa.
- Backend không được đóng gói (`[tool.uv] package = false`).

## Hệ quả

- Một công cụ cho môi trường ảo, cài đặt và khóa phiên bản.
- Người phát triển phải cài `uv`.
- Cấu hình Pytest, Ruff và mypy cũng nằm trong `pyproject.toml`.

## Phương án đã cân nhắc

- **`pip` + `requirements.txt`:** bị loại. Không có lock file đầy đủ nếu không thêm công cụ khác.
- **Poetry:** bị loại. `uv` đã được cài trên máy phát triển và nhanh hơn.
