# ADR-0004: Lưu tiền bằng số nguyên, đơn vị VND

- Trạng thái: Đã chấp thuận (áp dụng khi triển khai module Finance)
- Ngày: 2026-11-14

## Bối cảnh

CLAUDE.md mục 4.3 cấm dùng `float` cho tiền. Đơn vị tiền tệ mặc định là VND, không có đơn vị lẻ.

## Quyết định

- Số tiền lưu bằng `BigInteger`, đơn vị đồng.
- Mỗi bản ghi tiền có cột `currency` (`CHAR(3)`, mặc định `VND`).
- API nhận và trả số tiền dưới dạng số nguyên.
- Mọi phép tính tiền do Backend thực hiện. LLM không tính toán.

## Hệ quả

- Phép cộng và so sánh chính xác tuyệt đối; không cần quy tắc làm tròn cho VND.
- Nếu sau này hỗ trợ tiền tệ có đơn vị lẻ, số tiền lưu theo đơn vị nhỏ nhất của tiền tệ đó. Quy tắc làm tròn sẽ được ghi bằng ADR mới.

## Phương án đã cân nhắc

- **`Numeric`/`Decimal`:** bị loại cho MVP. SQLite không có kiểu thập phân chính xác; SQLAlchemy phải chuyển qua số thực hoặc chuỗi.
