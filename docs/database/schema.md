# Schema database

Tài liệu này mô tả schema **đang tồn tại** trong database. Quy ước chung và thiết kế sơ bộ của các bảng chưa tạo nằm trong [database-architecture.md](../architecture/database-architecture.md).

- Revision hiện tại: `5d1d9ce9ace0` — `create finance tables and pending actions`
- Migration: `backend/alembic/versions/`

## Quy ước áp dụng cho mọi bảng

- `id`: `Uuid`, khóa chính, sinh bởi ứng dụng.
- `created_at`, `updated_at`: thời điểm UTC, `NOT NULL`. `updated_at` tự cập nhật khi bản ghi thay đổi qua ORM.
- Giá trị liệt kê lưu dạng chuỗi; tính hợp lệ do ứng dụng kiểm tra.

## `users` — module `users`

Chủ sở hữu dữ liệu cá nhân.

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK `pk_users` |
| `display_name` | String(100) | Không | |
| `created_at` | DateTime | Không | |
| `updated_at` | DateTime | Không | |

Dữ liệu khởi tạo: một người dùng mặc định, ID `00000000-0000-0000-0000-000000000001`.

## `conversations` — module `memory`

Một phiên hội thoại.

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK `pk_conversations` |
| `user_id` | Uuid | Không | FK → `users.id`, `ON DELETE RESTRICT` |
| `title` | String(200) | Có | |
| `created_at` | DateTime | Không | |
| `updated_at` | DateTime | Không | |

Index: `ix_conversations_user_id_updated_at (user_id, updated_at)`.

## `messages` — module `memory`

Một tin nhắn hoặc một bản ghi thực thi Tool trong hội thoại.

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK `pk_messages` |
| `conversation_id` | Uuid | Không | FK → `conversations.id`, `ON DELETE CASCADE` |
| `sequence` | Integer | Không | Thứ tự trong hội thoại, bắt đầu từ 0 |
| `role` | String(20) | Không | `user`, `assistant`, `tool`, `system` |
| `content` | Text | Không | |
| `tool_name` | String(100) | Có | Có giá trị khi `role = tool` |
| `metadata` | JSON | Có | Thuộc tính ORM tên `meta` |
| `created_at` | DateTime | Không | |

Ràng buộc:

- Unique `uq_messages_conversation_id_sequence (conversation_id, sequence)`.
- Check `ck_messages_sequence_non_negative`: `sequence >= 0`.

Bảng này không có `updated_at`: tin nhắn không được sửa sau khi tạo.

## `memories` — module `memory`

Thông tin cá nhân dài hạn.

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK `pk_memories` |
| `user_id` | Uuid | Không | FK → `users.id`, `ON DELETE RESTRICT` |
| `category` | String(50) | Không | `preference`, `habit`, `goal`, `fact` |
| `content` | Text | Không | |
| `source` | String(20) | Không | `user_confirmed`, `ai_inferred` |
| `source_message_id` | Uuid | Có | FK → `messages.id`, `ON DELETE SET NULL` |
| `created_at` | DateTime | Không | |
| `updated_at` | DateTime | Không | |

Index: `ix_memories_user_id_category (user_id, category)`.

## Hành vi khi xóa

| Xóa | Kết quả |
| --- | --- |
| `conversations` | Mọi `messages` của hội thoại bị xóa theo |
| `messages` | `memories.source_message_id` liên quan được đặt `NULL`; Memory được giữ lại |
| `users` đang có dữ liệu | Bị từ chối |
| `conversations` | Mọi `ai_pending_actions` của hội thoại bị xóa theo |
| `transaction_categories` đang được dùng | Bị từ chối |

## `transaction_categories` — module `finance`

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `user_id` | Uuid | Không | FK → `users.id`, `RESTRICT` |
| `name` | String(60) | Không | |
| `kind` | String(20) | Không | `income`, `expense` |
| `created_at`, `updated_at` | DateTime | Không | |

Unique `uq_transaction_categories_user_id_kind_name`. Dữ liệu khởi tạo: 8 danh mục chi, 3 danh mục thu cho người dùng mặc định.

## `transactions` — module `finance`

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `user_id` | Uuid | Không | FK → `users.id`, `RESTRICT` |
| `category_id` | Uuid | Có | FK → `transaction_categories.id`, `RESTRICT`. Luôn trống với `adjustment` |
| `kind` | String(20) | Không | `income`, `expense`, `adjustment` |
| `amount` | BigInteger | Không | Đồng. Check `ck_transactions_amount_not_zero`. Chỉ `adjustment` được âm (kiểm tra ở service) |
| `currency` | String(3) | Không | `VND` |
| `occurred_on` | Date | Không | |
| `note` | String(500) | Có | |
| `created_at`, `updated_at` | DateTime | Không | |

Index `ix_transactions_user_id_occurred_on`.

## `budgets` — module `finance`

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `user_id` | Uuid | Không | FK → `users.id`, `RESTRICT` |
| `category_id` | Uuid | Có | FK → `transaction_categories.id`, `RESTRICT`. Trống: ngân sách tổng |
| `month` | Date | Không | Luôn là ngày 1 của tháng |
| `amount` | BigInteger | Không | Check `ck_budgets_amount_positive` |
| `currency` | String(3) | Không | `VND` |
| `created_at`, `updated_at` | DateTime | Không | |

Index `ix_budgets_user_id_month`. Mỗi tháng chỉ một ngân sách cho mỗi danh mục (kể cả ngân sách tổng): kiểm tra ở service, vì SQLite coi các giá trị NULL là khác nhau trong ràng buộc unique.

## `ai_pending_actions` — module `ai`

Thay đổi do trợ lý đề xuất, chờ người dùng xác nhận.

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `user_id` | Uuid | Không | FK → `users.id`, `RESTRICT` |
| `conversation_id` | Uuid | Không | FK → `conversations.id`, `CASCADE` |
| `tool_name` | String(100) | Không | |
| `arguments` | JSON | Không | Tham số đã kiểm tra; được kiểm tra lại khi xác nhận |
| `summary` | Text | Không | Câu mô tả hiển thị cho người dùng |
| `status` | String(20) | Không | `pending`, `confirmed`, `cancelled`, `failed` |
| `result` | JSON | Có | Kết quả khi `confirmed` |
| `error_code`, `error_message` | String(100), Text | Có | Khi `failed` |
| `resolved_at` | DateTime | Có | |
| `created_at`, `updated_at` | DateTime | Không | |

Index `ix_ai_pending_actions_user_id_status`.

## `travel_plans` — module `travel`

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `user_id` | Uuid | Không | FK → `users.id`, `RESTRICT` |
| `title` | String(120) | Không | |
| `destination_name` | String(200) | Có | Điểm đến: tên và tọa độ luôn có đủ cả ba hoặc không có |
| `destination_lat`, `destination_lon` | Float | Có | Tọa độ WGS84 |
| `start_date`, `end_date` | Date | Có | Check `ck_travel_plans_dates_in_order` |
| `note` | Text | Có | |
| `created_at`, `updated_at` | DateTime | Không | |

Index `ix_travel_plans_user_id_start_date`.

## `itinerary_items` — module `travel`

| Cột | Kiểu | Null | Ghi chú |
| --- | --- | --- | --- |
| `id` | Uuid | Không | PK |
| `plan_id` | Uuid | Không | FK → `travel_plans.id`, `CASCADE` (hoạt động là thành phần của kế hoạch) |
| `day` | Date | Có | Phải nằm trong khoảng ngày của kế hoạch (kiểm tra ở service) |
| `start_time` | Time | Có | |
| `position` | Integer | Không | Thứ tự thêm, dùng khi trùng ngày và giờ |
| `title` | String(200) | Không | |
| `place_name`, `place_lat`, `place_lon` | String(200), Float, Float | Có | Địa điểm, quy ước như điểm đến |
| `note` | Text | Có | |
| `created_at`, `updated_at` | DateTime | Không | |

Index `ix_itinerary_items_plan_id_day`. Xóa kế hoạch xóa luôn các hoạt động của nó.

## Bảng chưa tạo

Bảng của module Food và Dashboard được tạo khi các module đó được triển khai.
