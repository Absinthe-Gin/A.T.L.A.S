# Tài liệu API

- Địa chỉ gốc khi phát triển: `http://127.0.0.1:8710`
- Tiền tố: `/api/v1`
- Định dạng: JSON, UTF-8
- Tài liệu tương tác (không có ở Production): `GET /docs`, schema tại `GET /openapi.json`

Chưa có authentication. Mọi request được thực hiện dưới danh nghĩa người dùng cục bộ mặc định.

## Quy ước chung

### Request ID

Mọi response có header `X-Request-ID`. Client có thể gửi header này trong request; giá trị được dùng lại nếu chỉ gồm chữ, số, dấu gạch ngang và dài tối đa 64 ký tự. Dùng giá trị này để tìm log của request.

### Lỗi

Mọi lỗi trả cùng một cấu trúc:

```json
{
  "error": {
    "code": "conversation_not_found",
    "message": "Không tìm thấy cuộc hội thoại.",
    "details": [],
    "request_id": "0c1f7e0e6f0b4d3f9a1f3b6f2c5d7e9a"
  }
}
```

| Trường | Ý nghĩa |
| --- | --- |
| `code` | Định danh ổn định của lỗi. Client phân nhánh theo trường này |
| `message` | Thông điệp hiển thị được cho người dùng |
| `details` | Danh sách `{field, message}`; có nội dung với lỗi validation |
| `request_id` | Trùng với header `X-Request-ID` |

Mã lỗi chung:

| HTTP | `code` | Tình huống |
| --- | --- | --- |
| 404 | `not_found` | Đường dẫn không tồn tại |
| 405 | `method_not_allowed` | Sai HTTP method |
| 422 | `validation_error` | Dữ liệu request không hợp lệ |
| 500 | `internal_server_error` | Lỗi chưa lường trước. Không kèm chi tiết nội bộ |
| 500 | `default_user_missing` | Database chưa chạy migration |

## `GET /api/v1/health`

Báo trạng thái ứng dụng.

Response `200` khi database hoạt động, `503` khi database lỗi. Hai trường hợp có cùng cấu trúc:

```json
{
  "status": "ok",
  "environment": "development",
  "version": "0.1.0",
  "checks": {
    "database": "ok",
    "llm": { "status": "unavailable", "provider": "ollama" }
  }
}
```

| Trường | Giá trị |
| --- | --- |
| `status` | `ok`, `degraded` |
| `checks.database` | `ok`, `error` |
| `checks.llm.status` | `ok`, `unavailable` |
| `checks.llm.provider` | `ollama`, `mock` |

`checks.llm` chỉ mang tính thông tin. LLM không sẵn sàng không làm `status` thành `degraded`.

## `POST /api/v1/chat`

Gửi một tin nhắn cho trợ lý và nhận câu trả lời.

Request:

```json
{
  "message": "Xin chào",
  "conversation_id": null
}
```

| Trường | Kiểu | Bắt buộc | Ghi chú |
| --- | --- | --- | --- |
| `message` | string | Có | 1–4000 ký tự; không chỉ gồm khoảng trắng; khoảng trắng đầu và cuối bị bỏ |
| `conversation_id` | UUID | Không | Bỏ trống để bắt đầu hội thoại mới |

Response `200`:

```json
{
  "conversation_id": "f0ab8d39-d133-48b6-90bb-b9d2a24b15d3",
  "message_id": "e1af2e90-56b4-4674-bc8e-7b9c9c9f71bc",
  "reply": "Chào bạn!",
  "intent": "general",
  "tool_calls": []
}
```

| Trường | Ý nghĩa |
| --- | --- |
| `conversation_id` | Hội thoại chứa tin nhắn. Gửi lại giá trị này để tiếp tục hội thoại |
| `message_id` | ID tin nhắn của trợ lý |
| `reply` | Câu trả lời |
| `intent` | Ý định được nhận diện: tên domain của Tool, `general`, hoặc `unknown` |
| `tool_calls` | Các Tool đã chạy trong lượt này: `{name, status}`, `status` là `success` hoặc `error` |

Lỗi:

| HTTP | `code` | Tình huống |
| --- | --- | --- |
| 404 | `conversation_not_found` | `conversation_id` không tồn tại hoặc thuộc người dùng khác |
| 422 | `validation_error` | `message` hoặc `conversation_id` không hợp lệ |
| 502 | `llm_request_failed` | Dịch vụ AI trả lỗi |
| 502 | `llm_invalid_response` | Dịch vụ AI trả dữ liệu sai cấu trúc |
| 503 | `llm_not_configured` | Chưa đặt `OLLAMA_MODEL` |
| 503 | `llm_unavailable` | Không kết nối được tới dịch vụ AI |
| 504 | `llm_timeout` | Dịch vụ AI không phản hồi trong `LLM_TIMEOUT_SECONDS` |

Khi dịch vụ AI lỗi, tin nhắn của người dùng vẫn được lưu trong hội thoại.

Thời gian phản hồi phụ thuộc model. Client nên đặt timeout lớn hơn `LLM_TIMEOUT_SECONDS`.

## Endpoint chưa triển khai

Các endpoint sau thuộc quy ước trong CLAUDE.md mục 9 và sẽ được thêm cùng module tương ứng:
`/conversations`, `/memories`, `/transactions`, `/budgets`, `/finance/reports`, `/travel/plans`, `/places`, `/dashboard`.
