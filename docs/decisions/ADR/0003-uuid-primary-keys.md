# ADR-0003: Khóa chính UUID sinh ở tầng ứng dụng

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

ID của bản ghi xuất hiện trong URL, trong log và trong tham số Tool do LLM tạo. Database sẽ chuyển từ SQLite sang PostgreSQL.

## Quyết định

- Mọi bảng dùng khóa chính kiểu `Uuid` của SQLAlchemy.
- Giá trị là UUID phiên bản 4, sinh bởi ứng dụng (`UuidPrimaryKeyMixin`).

## Hệ quả

- ID không đoán được; LLM không thể suy ra ID của bản ghi khác bằng cách tăng số.
- ID có sẵn trước khi ghi database, thuận tiện cho log và cho việc tạo nhiều bản ghi liên quan.
- Kiểu `Uuid` ánh xạ `CHAR(32)` trên SQLite và `uuid` trên PostgreSQL; code không đổi.
- ID dài hơn và khó đọc hơn số nguyên khi debug thủ công.

## Phương án đã cân nhắc

- **Số nguyên tự tăng:** bị loại. Đoán được, và hành vi tự tăng khác nhau giữa SQLite và PostgreSQL.
