# Schema database

Tài liệu này mô tả schema **đang tồn tại** trong database. Quy ước chung và thiết kế sơ bộ của các bảng chưa tạo nằm trong [database-architecture.md](../architecture/database-architecture.md).

- Revision hiện tại: `d47fdc37c9e9` — `create users and memory tables`
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
| `users` đang có `conversations` hoặc `memories` | Bị từ chối |

## Bảng chưa tạo

`transaction_categories`, `transactions`, `budgets`, `travel_plans`, `itinerary_items` được tạo khi module Finance và Travel được triển khai.
