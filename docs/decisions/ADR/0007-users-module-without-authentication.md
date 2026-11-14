# ADR-0007: Module `users` và người dùng cục bộ mặc định, chưa có authentication

- Trạng thái: Đã chấp thuận
- Ngày: 2026-11-14

## Bối cảnh

MVP phục vụ một người dùng trên máy cá nhân. Authentication ảnh hưởng kiến trúc và cần phê duyệt riêng. Tuy vậy, mọi dữ liệu cá nhân cần có chủ sở hữu để việc bổ sung nhiều người dùng về sau không đòi hỏi sửa mọi bảng.

## Quyết định

- Thêm module `users`, sở hữu bảng `users`. Module này đã được bổ sung vào CLAUDE.md mục 3.2.
- Migration đầu tiên tạo một người dùng mặc định với ID cố định `00000000-0000-0000-0000-000000000001`.
- Mọi bảng dữ liệu cá nhân có cột `user_id` trỏ tới `users.id`.
- Chưa triển khai authentication. Backend lắng nghe `127.0.0.1` (giá trị mặc định của `API_HOST`).

## Hệ quả

- Khi bổ sung authentication, chỉ cần thay cách xác định người dùng hiện tại; schema và nghiệp vụ không đổi.
- **Rủi ro:** bất kỳ tiến trình nào trên máy đều gọi được API. Không được mở Backend ra mạng khi chưa có authentication.

## Phương án đã cân nhắc

- **Không có bảng `users`:** bị loại. Thêm `user_id` về sau đòi hỏi migration trên mọi bảng có dữ liệu.
- **Đặt bảng `users` trong module `memory`:** bị loại. Finance và Travel sẽ phụ thuộc Memory mà không có lý do nghiệp vụ.
