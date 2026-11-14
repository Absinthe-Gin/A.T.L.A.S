# ADR-0005: LLM Provider Adapter và vòng lặp Tool calling tự xây

- Trạng thái: Đã chấp thuận (triển khai ở Phase 4)
- Ngày: 2026-11-14

## Bối cảnh

Ollama là LLM Provider ban đầu và có thể bị thay thế. CLAUDE.md yêu cầu Single Agent, Multiple Tools, và yêu cầu validation cùng log cho từng bước. Framework AI (LangChain, LangGraph) không được dùng khi chưa có nhu cầu thực tế.

## Quyết định

- Định nghĩa interface `LLMProvider` với kiểu dữ liệu trung lập nhà cung cấp.
- `OllamaProvider` và `MockLLMProvider` là hai implementation đầu tiên.
- Orchestrator tự điều khiển vòng lặp Tool calling, có giới hạn số vòng.
- Provider được chọn theo cấu hình `LLM_PROVIDER`.

## Hệ quả

- Thêm nhà cung cấp mới chỉ cần viết một adapter.
- Mọi test AI chạy với `MockLLMProvider`; không cần Ollama.
- Hệ thống tự chịu trách nhiệm về vòng lặp, timeout và xử lý lỗi. Khối lượng code này nhỏ và được kiểm thử trực tiếp.

## Phương án đã cân nhắc

- **LangChain/LangGraph:** bị loại. Dependency lớn, che khuất bước validation và log mà dự án phải kiểm soát.
- **Gọi Ollama trực tiếp từ Orchestrator:** bị loại. Vi phạm CLAUDE.md mục 6.3 và không mock được.
