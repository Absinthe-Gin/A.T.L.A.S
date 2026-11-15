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

## Đề xuất thay đổi của trợ lý

Tool có tác dụng ghi (ví dụ `finance_create_transaction`) không chạy ngay. `POST /api/v1/chat` trả đề xuất trong `pending_actions`:

```json
{
  "pending_actions": [
    {
      "id": "6f1c…",
      "tool_name": "finance_create_transaction",
      "summary": "Ghi chi 50.000 ₫, danh mục Ăn uống, ngày 15/11/2026.",
      "status": "pending",
      "error_message": null
    }
  ]
}
```

`tool_calls` của Tool đó có `status: "pending"`. Không có gì được lưu cho đến khi người dùng xác nhận.

| Method | Đường dẫn | Tác dụng |
| --- | --- | --- |
| `POST` | `/api/v1/chat/actions/{id}/confirm` | Thực hiện đề xuất. Tham số được kiểm tra lại. Trả đề xuất với `status` là `confirmed` hoặc `failed` (kèm `error_message`) |
| `POST` | `/api/v1/chat/actions/{id}/cancel` | Hủy đề xuất. Trả `status: "cancelled"` |

| HTTP | `code` | Tình huống |
| --- | --- | --- |
| 404 | `pending_action_not_found` | Không có đề xuất, hoặc đề xuất của người dùng khác |
| 409 | `pending_action_resolved` | Đề xuất đã được xác nhận hoặc hủy trước đó |

## Tài chính

Mọi số tiền là **số nguyên, đơn vị đồng (VND)**. Số thực bị từ chối. Mọi tổng số do Backend tính.

Tham số `month` có dạng `YYYY-MM`; bỏ trống là tháng hiện tại.

### Danh mục

| Method | Đường dẫn | Ghi chú |
| --- | --- | --- |
| `GET` | `/api/v1/finance/categories?kind=` | `kind`: `income`, `expense`, bỏ trống: tất cả |
| `POST` | `/api/v1/finance/categories` | `{name, kind}`. Tên trùng (không phân biệt hoa thường) trong cùng loại: 409 `category_name_taken` |
| `PATCH` | `/api/v1/finance/categories/{id}` | `{name}` |
| `DELETE` | `/api/v1/finance/categories/{id}` | 204. Đang được giao dịch hoặc ngân sách dùng: 409 `category_in_use` |

Migration tạo sẵn 8 danh mục chi và 3 danh mục thu cho người dùng cục bộ.

### Giao dịch

| Method | Đường dẫn | Ghi chú |
| --- | --- | --- |
| `GET` | `/api/v1/transactions?month=&kind=&category_id=&limit=&offset=` | `Page`, mới nhất trước. `limit` 1–100, mặc định 50 |
| `POST` | `/api/v1/transactions` | 201 |
| `PATCH` | `/api/v1/transactions/{id}` | Chỉ đổi các trường được gửi |
| `DELETE` | `/api/v1/transactions/{id}` | 204 |

```json
{
  "kind": "expense",
  "amount": 45000,
  "category_id": "…",
  "occurred_on": "2026-11-15",
  "note": "Phở"
}
```

| Quy tắc | Lỗi |
| --- | --- |
| `income`, `expense`: `amount` > 0 | 422 `invalid_amount` |
| `adjustment`: `amount` ≠ 0, được âm | 422 `invalid_amount` |
| `adjustment` không có danh mục | 422 `adjustment_has_no_category` |
| Danh mục phải cùng loại với giao dịch | 422 `category_kind_mismatch` |
| \|`amount`\| ≤ 10^15 | 422 `validation_error` |

### Ngân sách

| Method | Đường dẫn | Ghi chú |
| --- | --- | --- |
| `GET` | `/api/v1/budgets?month=` | Kèm `spent`, `remaining`, `used_percent`, `over_budget` |
| `POST` | `/api/v1/budgets` | `{month, category_id, amount}`. `category_id` trống: ngân sách tổng. Trùng tháng và mục: 409 `budget_exists` |
| `PATCH` | `/api/v1/budgets/{id}` | `{amount}` |
| `DELETE` | `/api/v1/budgets/{id}` | 204 |

Ngân sách chỉ áp dụng cho danh mục chi. `used_percent` là phần trăm nguyên, làm tròn xuống; trên 100 là vượt ngân sách.

### Báo cáo

`GET /api/v1/finance/reports/monthly?month=` trả `income_total`, `expense_total`, `adjustment_total`, `net` (= thu − chi + điều chỉnh), `transaction_count`, `expense_by_category` (lớn nhất trước; khoản không có danh mục là "Chưa phân loại") và `budgets`.

## Du lịch

### Kế hoạch và lịch trình

| Method | Đường dẫn | Ghi chú |
| --- | --- | --- |
| `GET` | `/api/v1/travel/plans?limit=&offset=` | `Page`. Kế hoạch có ngày đứng trước, theo ngày đi; kèm `item_count`. `limit` 1–100, mặc định 20 |
| `POST` | `/api/v1/travel/plans` | 201, trả `PlanDetail` |
| `GET` | `/api/v1/travel/plans/{id}` | `PlanDetail`: kế hoạch và `items` theo ngày, giờ |
| `PATCH` | `/api/v1/travel/plans/{id}` | Chỉ đổi các trường được gửi; `"destination": null` bỏ điểm đến |
| `DELETE` | `/api/v1/travel/plans/{id}` | 204, xóa cả lịch trình |
| `POST` | `/api/v1/travel/plans/{id}/items` | 201 |
| `PATCH` | `/api/v1/travel/plans/{id}/items/{item_id}` | |
| `DELETE` | `/api/v1/travel/plans/{id}/items/{item_id}` | 204 |

```json
{
  "title": "Đà Lạt cuối năm",
  "destination": {"name": "Đà Lạt", "lat": 11.9404, "lon": 108.4583},
  "start_date": "2026-12-01",
  "end_date": "2026-12-03",
  "note": null
}
```

| Quy tắc | Lỗi |
| --- | --- |
| `end_date` ≥ `start_date` | 422 `invalid_date_range` |
| `day` của hoạt động nằm trong khoảng ngày của kế hoạch | 422 `day_outside_plan` |
| Kế hoạch hoặc hoạt động không tồn tại | 404 `travel_plan_not_found`, `itinerary_item_not_found` |

### Thông tin trực tiếp

Dữ liệu lấy từ dịch vụ ngoài miễn phí. Lỗi của dịch vụ ngoài trả 502, 503 hoặc 504 với `code` dạng `<dịch vụ>_<lỗi>`, ví dụ `nominatim_unavailable`.

| Method | Đường dẫn | Nguồn | Ghi chú |
| --- | --- | --- | --- |
| `GET` | `/api/v1/places/search?q=&limit=` | OpenStreetMap: Nominatim, Photon khi Nominatim lỗi | `q` 2–200 ký tự, `limit` 1–10. Danh sách `{name, display_name, lat, lon, category, type, osm_type, osm_id}` |
| `GET` | `/api/v1/travel/weather?lat=&lon=&days=` | Open-Meteo | `days` 1–16, mặc định 7. `current` và `daily`, mô tả bằng tiếng Việt |
| `GET` | `/api/v1/travel/transport` | OSRM, SerpApi | Xem dưới |

Tham số của `/travel/transport`: `origin_name`, `origin_lat`, `origin_lon`, `destination_name`, `destination_lat`, `destination_lon`, `travel_date` (bắt buộc); `adults` (1–9, mặc định 1); `origin_airport`, `destination_airport` (mã IATA, không bắt buộc).

Mỗi phần của kết quả độc lập; một nguồn lỗi không làm hỏng phần còn lại:

- `road`: quãng đường và thời gian lái xe (OSRM). `status`: `ok`, `no_route`, `unavailable`.
- `flights`: sân bay gần nhất (trong 150 km) ở mỗi đầu, hoặc mã IATA người dùng nhập. `status`:
  - `ok`: có giá từ Google Flights qua SerpApi, rẻ nhất trước, tối đa 10;
  - `not_configured`: chưa đặt `SERPAPI_API_KEY`, chỉ có `search_url` tới Google Flights;
  - `no_airport`, `too_close` (dưới 100 km hoặc cùng sân bay), `unavailable`.
- `ground_links`: liên kết dsvn.vn (tàu) và Vexere (xe khách). Atlas không có giờ chạy và giá vé tàu, xe vì các nhà cung cấp này không có API công khai miễn phí.

## Ẩm thực

Món đặc sản theo khu vực là gợi ý biên tập của Atlas, không phải số liệu thống kê. Quán ăn lấy từ OpenStreetMap: qua Photon, hoặc Overpass API khi Photon lỗi. Tên món được so khớp không phân biệt hoa thường và dấu tiếng Việt ("bun bo" khớp "Bún bò"). Atlas chỉ tìm quán có **tên chứa món**; quán không được ghi nhận trong OpenStreetMap sẽ không xuất hiện.

| Method | Đường dẫn | Ghi chú |
| --- | --- | --- |
| `GET` | `/api/v1/food/recommendations?lat=&lon=` | Món đặc sản của miền gần điểm đã cho nhất (Bắc, Trung, Nam). Không gọi dịch vụ ngoài |
| `GET` | `/api/v1/food/restaurants?dish=&lat=&lon=&radius_m=&limit=` | `dish` 2–120 ký tự, chỉ gồm chữ, số, khoảng trắng và dấu gạch ngang (khác: 422 `invalid_dish_query`). `radius_m` 100–20000, mặc định 5000. `limit` 1–20, mặc định 10. Quán gần nhất trước, kèm `distance_km` |

`/food/restaurants` trả `status`:

- `ok`: có quán;
- `no_results`: không có quán nào có tên chứa món trong bán kính (kèm `message`);
- `unavailable`: Overpass lỗi hoặc quá tải. Trả 200 với `status` này, không làm hỏng trang.

## Endpoint chưa triển khai

`/conversations`, `/memories`, `/dashboard`.
