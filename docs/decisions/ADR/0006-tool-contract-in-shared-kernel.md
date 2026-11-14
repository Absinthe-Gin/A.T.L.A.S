# ADR-0006: Tool contract trong shared kernel, đăng ký tại composition root

- Trạng thái: Đã chấp thuận (triển khai ở Phase 4)
- Ngày: 2026-11-14

## Bối cảnh

AI Core cần gọi nghiệp vụ của Finance, Travel, Food và Memory. CLAUDE.md cấm AI Core phụ thuộc implementation của module nghiệp vụ và cấm phụ thuộc vòng. AI Core lại cần module Memory để nạp ngữ cảnh, trong khi Memory cũng cung cấp Tool.

## Quyết định

- Tool contract (`Tool`, `ToolSpec`, `ToolContext`, `ToolResult`) nằm tại `app/shared/tools.py`.
- Module nghiệp vụ định nghĩa Tool trong `tools.py` của chính nó.
- `app/bootstrap.py` thu thập Tool và đăng ký vào `ToolRegistry`.
- AI Core chỉ biết Tool contract và Registry.

## Hệ quả

- Hướng phụ thuộc: module nghiệp vụ → `shared`; `ai` → `shared` và `memory.public`. Không có vòng.
- Thêm module mới không cần sửa AI Core.
- `bootstrap.py` là nơi duy nhất biết mọi module. Đây là trách nhiệm có chủ đích của composition root.

## Phương án đã cân nhắc

- **Tool contract trong module `ai`:** bị loại. Memory vừa được `ai` import vừa phải import `ai`, tạo vòng phụ thuộc.
- **AI Core import trực tiếp service nghiệp vụ:** bị loại. Vi phạm ranh giới module.
