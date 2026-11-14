# CLAUDE.md — QUY TẮC PHÁT TRIỂN DỰ ÁN AI PERSONAL ASSISTANT

> **TÀI LIỆU BẮT BUỘC TUÂN THỦ**
>
> File này quy định các nguyên tắc kiến trúc, lập trình, kiểm thử, bảo mật và quy trình làm việc áp dụng cho toàn bộ dự án.
>
> Claude Code phải đọc, hiểu và tuân thủ các quy tắc trong file này trước khi thực hiện bất kỳ thay đổi nào đối với mã nguồn.
>
> **Không được tự ý bỏ qua, thay đổi hoặc diễn giải lại các quy tắc bắt buộc nếu chưa có sự chấp thuận của người dùng.**
>
> Mục 1–22 là nguyên tắc. **Mục 23 là quy ước cụ thể của codebase hiện tại** (cấu trúc thư mục, tên file, lệnh, địa chỉ chạy). Khi viết code, phải làm đúng mục 23.

---

# 1. TỔNG QUAN DỰ ÁN

## 1.1. Mục tiêu

AI Personal Assistant là ứng dụng trợ lý cá nhân sử dụng AI, hỗ trợ người dùng quản lý và thực hiện các công việc thường ngày thông qua giao diện Chat kết hợp Dashboard.

Các chức năng chính:

- **AI Chat:** Giao tiếp với trợ lý AI, tiếp nhận yêu cầu và điều phối công cụ.
- **Travel Planner:** Lập kế hoạch, lịch trình và quản lý chuyến đi.
- **Food Discovery:** Tìm kiếm, khám phá và đề xuất địa điểm ăn uống.
- **Finance Assistant:** Quản lý thu chi, ngân sách và báo cáo tài chính cá nhân.
- **Personal Memory:** Lưu trữ và truy xuất thông tin cá nhân, lịch sử hội thoại.
- **Dashboard:** Tổng hợp thông tin và hiển thị dữ liệu trực quan.

## 1.2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Frontend | ReactJS, TypeScript, Vite |
| UI | Tailwind CSS |
| Backend | Python, FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database Migration | Alembic |
| Database MVP | SQLite |
| AI Runtime | Ollama |
| Map | Leaflet, OpenStreetMap |
| Testing Backend | Pytest |
| Testing Frontend | Vitest, React Testing Library |
| Routing Frontend | React Router |
| HTTP client Frontend | Axios |
| HTTP client Backend | httpx |
| Database driver | aiosqlite (SQLAlchemy async) |
| Quản lý dependency Backend | uv (`pyproject.toml`, `uv.lock`) |
| Lint, format, type check Backend | Ruff, mypy (strict) |
| Lint Frontend | oxlint |
| Version Control | Git |

**Nguyên tắc:** Không tự ý thay đổi công nghệ cốt lõi, thêm framework hoặc thư viện lớn khi chưa phân tích lý do và được người dùng chấp thuận.

---

# 2. THỨ TỰ ƯU TIÊN VÀ NGUYÊN TẮC TUÂN THỦ

Khi có xung đột giữa các yêu cầu, phải ưu tiên theo thứ tự:

1. Yêu cầu trực tiếp và mới nhất của người dùng.
2. Các quy tắc bắt buộc trong file CLAUDE.md.
3. Tài liệu kiến trúc và các quyết định đã được phê duyệt (ADR).
4. Quy ước của module và tài liệu kỹ thuật liên quan.
5. Quy ước mặc định của framework và cộng đồng.

Các nguyên tắc không được vi phạm:

- Không tự ý thay đổi kiến trúc tổng thể.
- Không tự ý thay đổi công nghệ nền tảng.
- Không viết code khi chưa hiểu cấu trúc và luồng xử lý hiện tại.
- Không tạo code trùng lặp khi đã có chức năng tương đương.
- Không đặt logic nghiệp vụ trong sai tầng kiến trúc.
- Không để AI trực tiếp quyết định hoặc thực hiện các phép tính nghiệp vụ quan trọng.
- Không tự ý xóa, ghi đè hoặc làm mất dữ liệu.
- Không bỏ qua lỗi, cảnh báo quan trọng hoặc kết quả kiểm thử thất bại.
- Không tuyên bố hoàn thành nếu chưa xác minh kết quả.
- Không triển khai giải pháp phức tạp hơn mức cần thiết.

Nếu không thể đáp ứng một quy tắc, phải dừng tại phần liên quan, giải thích nguyên nhân, đánh giá ảnh hưởng và đề xuất phương án xử lý. Không được âm thầm làm khác đi.

---

# 3. NGUYÊN TẮC KIẾN TRÚC HỆ THỐNG

## 3.1. Kiến trúc tổng thể

Bắt buộc sử dụng:

- Modular Monolith.
- Clean Architecture theo hướng thực dụng.
- Separation of Concerns.
- Dependency Inversion.
- Single Responsibility Principle.
- Explicit Dependencies.

Không triển khai Microservices trong giai đoạn hiện tại.

Không áp dụng máy móc các design pattern. Chỉ sử dụng abstraction, interface, factory, repository hoặc dependency injection khi có lý do kỹ thuật rõ ràng.

## 3.2. Phân chia module

Các module nghiệp vụ phải có ranh giới rõ ràng:

```text
AI Personal Assistant
│
├── AI Core
│   ├── Orchestrator
│   ├── Intent Classification
│   ├── Tool Registry
│   ├── Tool Execution
│   └── LLM Provider
│
├── Personal Memory
│   ├── Conversation Memory
│   ├── Long-term Memory
│   └── Memory Retrieval
│
├── Finance
│   ├── Transactions
│   ├── Categories
│   ├── Budgets
│   └── Reports
│
├── Travel
│   ├── Travel Plans
│   ├── Itineraries
│   └── Travel Recommendations
│
├── Food Discovery
│   ├── Place Search
│   ├── Place Details
│   └── Recommendations
│
├── Dashboard
│   ├── Overview
│   └── Aggregated Data
│
├── Users
│   └── Current User (người dùng cục bộ mặc định, chưa có authentication)
│
└── Health
    └── Health Check (module kỹ thuật, không chứa nghiệp vụ)
```

Trạng thái triển khai: `health`, `users`, `memory`, `ai` đã có code. `finance`, `travel`, `food`, `dashboard` chưa có; chỉ tạo thư mục module khi có yêu cầu triển khai.

Quy định:

- Mỗi module phải chịu trách nhiệm cho một nhóm nghiệp vụ cụ thể.
- Không để một module phụ thuộc trực tiếp vào cấu trúc nội bộ của module khác.
- Giao tiếp giữa các module thông qua public interface, service hoặc contract đã xác định.
- Public interface của một module là file `public.py` của module đó. Module khác chỉ được import `app.modules.<module>.public`.
- Không truy cập trực tiếp repository hoặc database của module khác.
- Không tạo circular dependency.
- Không để module Dashboard chứa logic nghiệp vụ của Finance, Travel hoặc Food Discovery.
- Không để AI Core phụ thuộc trực tiếp vào implementation cụ thể của các module nghiệp vụ.

## 3.3. Quy tắc phân tầng Backend

Backend phải phân chia trách nhiệm theo các tầng:

| Tầng | Trách nhiệm | Không được làm |
|---|---|---|
| API / Router | Nhận request, trả response, khai báo endpoint | Chứa nghiệp vụ phức tạp |
| Schema | Validate và serialize dữ liệu | Truy cập database |
| Service / Use Case | Xử lý nghiệp vụ | Phụ thuộc HTTP Request/Response |
| Repository | Truy vấn và thao tác dữ liệu | Chứa logic nghiệp vụ |
| Model | Định nghĩa cấu trúc dữ liệu ORM | Chứa luồng xử lý nghiệp vụ |
| Provider / Adapter | Tích hợp dịch vụ bên ngoài | Đưa logic nghiệp vụ vào adapter |

Quy tắc bắt buộc:

- Router chỉ điều phối request đến service/use case.
- Service chịu trách nhiệm thực thi nghiệp vụ.
- Repository chịu trách nhiệm truy xuất dữ liệu.
- Pydantic Schema chịu trách nhiệm validate dữ liệu đầu vào và đầu ra.
- Không gọi database trực tiếp từ Router.
- Không viết SQL trực tiếp trong Router hoặc AI Orchestrator.
- Không trả ORM Model trực tiếp ra API.
- Không sử dụng một lớp cho quá nhiều trách nhiệm.

## 3.4. Quy tắc phân tầng Frontend

Frontend phải phân chia trách nhiệm rõ ràng:

| Thành phần | Trách nhiệm |
|---|---|
| Pages | Tổ chức màn hình theo route |
| Components | Hiển thị giao diện có thể tái sử dụng |
| Features | Chứa logic theo chức năng nghiệp vụ |
| Hooks | Đóng gói state và logic có thể tái sử dụng |
| Services / API | Giao tiếp với Backend |
| Types | Định nghĩa kiểu dữ liệu |
| Utils | Hàm tiện ích thuần |
| Stores | Quản lý global state khi thực sự cần thiết |

Quy định:

- Không viết toàn bộ logic trong component.
- Không gọi API trực tiếp tại nhiều component khác nhau.
- Không sao chép logic xử lý dữ liệu giữa các màn hình.
- Không sử dụng global state cho dữ liệu chỉ cần quản lý cục bộ.
- Không để component phụ thuộc trực tiếp vào implementation của Backend.
- Phải tách biệt dữ liệu API, trạng thái giao diện và logic hiển thị.
- Component phải có trách nhiệm rõ ràng và có thể kiểm thử độc lập khi phù hợp.

---

# 4. QUY TẮC LẬP TRÌNH BACKEND

## 4.1. Python

Bắt buộc:

- Sử dụng Type Hint cho function, method và biến quan trọng.
- Sử dụng Pydantic để validate dữ liệu đầu vào/đầu ra.
- Ưu tiên function và class có trách nhiệm rõ ràng.
- Sử dụng `async/await` nhất quán với các luồng I/O bất đồng bộ.
- Sử dụng context manager khi làm việc với tài nguyên cần đóng.
- Sử dụng cấu hình môi trường thay vì hardcode.
- Sử dụng `Decimal` hoặc kiểu dữ liệu chính xác phù hợp cho phép tính tiền.
- Định nghĩa exception có ý nghĩa thay vì sử dụng exception chung chung.
- Sử dụng logging thay cho `print()` trong code ứng dụng.

Không được:

- Sử dụng `except Exception: pass`.
- Nuốt lỗi mà không ghi nhận hoặc xử lý.
- Sử dụng biến global để lưu trạng thái nghiệp vụ.
- Hardcode API Key, mật khẩu hoặc thông tin nhạy cảm.
- Viết function quá dài và chứa nhiều trách nhiệm.
- Tạo class chỉ để bọc một function đơn giản mà không có lý do.
- Sử dụng `Any` tùy tiện để né tránh kiểm tra kiểu dữ liệu.

## 4.2. Database và ORM

Bắt buộc:

- Sử dụng SQLAlchemy để thao tác database.
- Sử dụng Alembic để quản lý migration.
- Tách biệt ORM Model và API Schema.
- Đặt tên bảng, cột, khóa và quan hệ nhất quán.
- Khai báo rõ ràng quan hệ giữa các bảng.
- Xác định rõ nullable, unique, index và foreign key.
- Sử dụng transaction cho các thao tác cần đảm bảo tính toàn vẹn dữ liệu.
- Kiểm tra ảnh hưởng dữ liệu trước khi thay đổi schema.
- Có chiến lược rollback cho migration khi phù hợp.

Không được:

- Sửa schema database bằng thao tác thủ công mà không cập nhật migration.
- Xóa cột hoặc bảng khi chưa đánh giá dữ liệu phụ thuộc.
- Sử dụng cascade delete tùy tiện.
- Truy vấn database trong vòng lặp gây N+1 query khi có thể tối ưu.
- Đưa dữ liệu nhạy cảm vào log.
- Để một request tạo ra nhiều lần ghi dữ liệu không cần thiết.

## 4.3. Quy tắc xử lý tiền tệ

Đây là quy tắc nghiệp vụ bắt buộc của Finance:

- Đơn vị tiền tệ mặc định: VND.
- Không sử dụng số thực `float` để lưu trữ hoặc tính toán tiền.
- Lưu số tiền bằng số nguyên (`BigInteger`), đơn vị đồng. API nhận và trả số tiền dạng số nguyên (ADR-0004).
- Mỗi bản ghi tiền có cột `currency` (`CHAR(3)`, mặc định `VND`).
- Thống nhất quy tắc làm tròn.
- Không để LLM tự tính tổng thu, chi, số dư hoặc ngân sách.
- Các phép tính tài chính phải được thực hiện bởi Backend.
- Phải kiểm thử các trường hợp số tiền bằng 0, số âm, giá trị lớn và dữ liệu biên.
- Phân biệt rõ giao dịch thu, chi và các loại điều chỉnh số dư.

---

# 5. QUY TẮC LẬP TRÌNH FRONTEND

Bắt buộc:

- Sử dụng TypeScript và ưu tiên strict type checking.
- Khai báo type/interface cho dữ liệu trao đổi với Backend.
- Sử dụng API service tập trung.
- Có trạng thái Loading, Empty, Error và Success cho các luồng dữ liệu phù hợp.
- Có cơ chế xử lý lỗi tập trung.
- Sử dụng component dùng chung khi có nhu cầu thực tế.
- Đảm bảo giao diện responsive.
- Sử dụng semantic HTML và hỗ trợ accessibility cơ bản.
- Quản lý form validation nhất quán.
- Phân biệt rõ server state và client state.

Không được:

- Sử dụng `any` tùy tiện.
- Gọi API trực tiếp từ nhiều nơi bằng các đoạn code trùng lặp.
- Đưa API URL vào nhiều component.
- Lưu dữ liệu nhạy cảm không cần thiết ở Local Storage.
- Dùng CSS inline tràn lan.
- Tạo component quá lớn, khó đọc và khó kiểm thử.
- Dùng index làm key cho danh sách có thể thay đổi thứ tự khi có định danh ổn định.
- Bỏ qua trạng thái lỗi của API.
- Chỉ hiển thị thông báo thành công mà không xác minh kết quả thực tế.

---

# 6. QUY TẮC PHÁT TRIỂN AI CORE

## 6.1. Nguyên tắc thiết kế

AI Core phải được thiết kế độc lập với các module nghiệp vụ.

Luồng xử lý chuẩn:

```text
User Message
    ↓
Conversation Context
    ↓
Memory Retrieval
    ↓
Intent Classification
    ↓
Tool Selection
    ↓
Input Validation
    ↓
Tool Execution
    ↓
Output Validation
    ↓
LLM Response Generation
    ↓
Save Conversation
```

Bắt buộc:

- Sử dụng mô hình Single Agent kết hợp Multiple Tools trong MVP.
- Tách biệt LLM Provider, Orchestrator và Tool.
- Mỗi Tool phải có input schema và output schema rõ ràng.
- Tool chỉ thực hiện một nhóm tác vụ cụ thể.
- Kiểm tra và validate dữ liệu trước khi thực thi Tool.
- Kiểm tra kết quả trả về trước khi đưa vào ngữ cảnh LLM.
- Có timeout và xử lý lỗi cho các thao tác gọi dịch vụ bên ngoài.
- Ghi nhận lịch sử thực thi Tool để phục vụ debug.
- Có cơ chế giới hạn số lần gọi Tool trong một lượt xử lý.
- Có cơ chế xử lý khi AI chọn sai Tool hoặc không chọn được Tool.

## 6.2. Phân tách AI và Business Logic

Đây là quy tắc tuyệt đối:

**LLM không được trực tiếp thực thi nghiệp vụ hoặc truy cập database.**

LLM chỉ được:

- Hiểu yêu cầu người dùng.
- Phân loại ý định.
- Đề xuất Tool phù hợp.
- Tạo tham số cho Tool.
- Tổng hợp kết quả trả về.
- Tạo câu trả lời bằng ngôn ngữ tự nhiên.

Backend mới là thành phần:

- Validate dữ liệu.
- Kiểm tra quyền thực thi.
- Thực hiện nghiệp vụ.
- Tính toán.
- Ghi và đọc dữ liệu.
- Kiểm tra tính toàn vẹn dữ liệu.

Không được:

- Cho phép LLM tự tạo và thực thi SQL tùy ý.
- Tin tưởng tuyệt đối vào tham số do LLM tạo.
- Cho phép LLM bỏ qua validation.
- Cho phép LLM tự suy diễn dữ liệu không có trong hệ thống.
- Để kết quả AI quyết định trực tiếp các thao tác có tác động đến dữ liệu mà không qua kiểm tra.

## 6.3. LLM Provider

Phải thiết kế theo hướng Provider Adapter.

Ví dụ:

```text
AI Core
   │
   ├── LLM Provider Interface
   │       │
   │       ├── Ollama Provider
   │       └── Future Provider
   │
   └── Orchestrator
```

Quy định:

- Không gọi Ollama trực tiếp từ các module nghiệp vụ.
- Không để logic phụ thuộc vào một model cụ thể.
- Có thể thay đổi hoặc bổ sung LLM Provider mà không phải sửa toàn bộ AI Core.
- Cấu hình model, temperature, timeout và các tham số liên quan thông qua config.
- Có cơ chế xử lý khi LLM không phản hồi hoặc trả về dữ liệu không hợp lệ.

## 6.4. AI Debugging

Mỗi lượt xử lý AI cần ghi nhận tối thiểu:

- Conversation ID.
- Message ID.
- Intent được nhận diện.
- Tool được lựa chọn.
- Input của Tool sau khi đã loại bỏ thông tin nhạy cảm.
- Thời gian thực thi.
- Trạng thái thành công/thất bại.
- Output hoặc thông tin lỗi phù hợp.
- LLM Provider và model được sử dụng.

Không ghi API Key, mật khẩu hoặc dữ liệu cá nhân nhạy cảm vào log.

---

# 7. QUY TẮC PERSONAL MEMORY

Phân biệt rõ hai loại Memory:

## 7.1. Conversation Memory

Lưu trữ:

- Hội thoại.
- Tin nhắn.
- Thời gian.
- Vai trò người gửi.
- Metadata cần thiết.

Phải đảm bảo có thể truy xuất theo Conversation ID.

## 7.2. Long-term Personal Memory

Lưu trữ các thông tin có giá trị sử dụng lâu dài, ví dụ:

- Sở thích.
- Thói quen.
- Mục tiêu cá nhân.
- Các thông tin người dùng cho phép lưu.
- Ngữ cảnh hữu ích cho các lần tương tác sau.

Quy định:

- Memory phải có nguồn gốc và thời gian tạo.
- Phân biệt thông tin được người dùng xác nhận với thông tin AI suy luận.
- Không tự động lưu mọi nội dung hội thoại thành Memory.
- Không để Memory cũ ghi đè thông tin mới khi chưa kiểm tra.
- Có cơ chế cập nhật, xóa và truy xuất Memory.
- Không sử dụng Memory không liên quan đến yêu cầu hiện tại.
- Không để dữ liệu của các cuộc hội thoại khác nhau bị trộn lẫn.

Không triển khai Vector Database trong MVP nếu chưa có nhu cầu thực tế được xác nhận.

---

# 8. QUY TẮC TÍCH HỢP DỊCH VỤ BÊN NGOÀI

Mọi dịch vụ bên ngoài phải được tích hợp thông qua Adapter hoặc Provider riêng.

Áp dụng cho:

- LLM.
- Bản đồ.
- Tìm kiếm địa điểm.
- Dịch vụ dữ liệu bên ngoài trong tương lai.

Bắt buộc:

- Không gọi API bên ngoài trực tiếp từ Business Service nếu có thể tách qua Adapter.
- Có timeout.
- Có xử lý lỗi mạng.
- Có validation dữ liệu trả về.
- Không giả định dữ liệu bên ngoài luôn đầy đủ.
- Ghi nhận nguồn dữ liệu khi cần thiết.
- Không hiển thị dữ liệu giả như dữ liệu thực.
- Có khả năng mock provider khi kiểm thử.

Không được:

- Phụ thuộc vào một nhà cung cấp duy nhất nếu không có lý do rõ ràng.
- Hardcode API Key.
- Để lỗi của dịch vụ bên ngoài làm sập toàn bộ ứng dụng.
- Giả định địa điểm luôn có rating, giá hoặc giờ mở cửa.

---

# 9. QUY TẮC API DESIGN

Bắt buộc:

- Sử dụng REST API nhất quán.
- Đặt tên endpoint theo tài nguyên.
- Sử dụng HTTP Method đúng mục đích.
- Có request schema và response schema.
- Chuẩn hóa lỗi API.
- Validate dữ liệu ở Backend.
- Có phân trang cho các danh sách có khả năng tăng trưởng.
- Có cơ chế lọc và sắp xếp khi cần thiết.
- Không trả về thông tin nội bộ không cần thiết.

Quy ước endpoint:

```text
/api/v1/chat
/api/v1/conversations
/api/v1/memories
/api/v1/transactions
/api/v1/budgets
/api/v1/finance/reports
/api/v1/travel/plans
/api/v1/places
/api/v1/dashboard
```

Quy định:

- Không thay đổi API contract mà không đánh giá ảnh hưởng đến Frontend.
- Khi thay đổi response schema, phải cập nhật type tương ứng ở Frontend.
- Không sử dụng một response format khác nhau tùy tiện giữa các module.
- Các lỗi nghiệp vụ phải có mã lỗi hoặc thông tin nhận diện phù hợp.

---

# 10. QUY TẮC DEBUGGING VÀ LOGGING

Đây là một trong những ưu tiên cao nhất của dự án.

Mọi code được viết phải hướng đến khả năng truy vết và xác định nguyên nhân lỗi.

## 10.1. Logging

Backend phải sử dụng logging có cấu trúc.

Mức log:

- DEBUG: Thông tin phục vụ debug.
- INFO: Sự kiện nghiệp vụ bình thường.
- WARNING: Tình huống bất thường nhưng chưa gây lỗi nghiêm trọng.
- ERROR: Lỗi xử lý.
- CRITICAL: Lỗi nghiêm trọng ảnh hưởng đến hệ thống.

Mỗi log cần có ngữ cảnh phù hợp:

- Timestamp.
- Log level.
- Module.
- Function hoặc operation.
- Request ID hoặc Correlation ID khi phù hợp.
- Thông tin lỗi.

Không sử dụng `print()` để thay thế logging trong code production.

## 10.2. Error Handling

Bắt buộc:

- Xử lý lỗi tại tầng phù hợp.
- Không che giấu lỗi.
- Không trả stack trace nội bộ ra Frontend.
- Phân biệt lỗi validation, lỗi nghiệp vụ, lỗi hệ thống và lỗi dịch vụ bên ngoài.
- Thông báo lỗi phải đủ rõ để người phát triển xác định nguyên nhân.
- Lỗi phải được ghi log với ngữ cảnh cần thiết.

## 10.3. Frontend Debugging

Bắt buộc:

- Có Error Boundary cho các khu vực giao diện phù hợp.
- Có cơ chế xử lý lỗi API tập trung.
- Có thông báo lỗi thân thiện với người dùng.
- Không chỉ sử dụng `console.log()` để debug.
- Không để lỗi của một component không liên quan làm hỏng toàn bộ ứng dụng.

## 10.4. Nguyên tắc sửa lỗi

Khi phát hiện bug:

1. Xác định cách tái hiện lỗi.
2. Xác định module và tầng phát sinh lỗi.
3. Phân tích nguyên nhân gốc (Root Cause).
4. Đánh giá các chức năng bị ảnh hưởng.
5. Đề xuất phương án sửa.
6. Thực hiện thay đổi tối thiểu nhưng giải quyết triệt để nguyên nhân.
7. Viết hoặc cập nhật test case tái hiện lỗi.
8. Chạy kiểm thử hồi quy liên quan.
9. Ghi nhận kết quả.

Không được sửa lỗi bằng cách thêm điều kiện tạm thời để che giấu nguyên nhân nếu chưa hiểu bản chất vấn đề.

---

# 11. QUY TẮC TESTING

**Không được coi một chức năng là hoàn thành nếu chưa có kiểm thử phù hợp.**

## 11.1. Backend Testing

Sử dụng Pytest.

Ưu tiên:

- Unit Test cho Business Logic.
- Service Test cho Use Case.
- API Test cho Endpoint.
- Integration Test cho Database và Provider.
- Mock các dịch vụ bên ngoài khi cần thiết.

Các trường hợp phải kiểm thử:

- Luồng thành công.
- Dữ liệu không hợp lệ.
- Dữ liệu thiếu.
- Dữ liệu biên.
- Dữ liệu không tồn tại.
- Lỗi database.
- Lỗi dịch vụ bên ngoài.
- Các tình huống ngoại lệ.

## 11.2. Frontend Testing

Sử dụng Vitest và React Testing Library.

Ưu tiên:

- Kiểm thử component.
- Kiểm thử custom hook.
- Kiểm thử trạng thái giao diện.
- Kiểm thử xử lý API.
- Kiểm thử các luồng người dùng quan trọng.

## 11.3. AI Testing

AI có tính không xác định nên không chỉ kiểm thử bằng cách so sánh nguyên văn câu trả lời.

Phải kiểm thử:

- Intent Classification.
- Tool Selection.
- Tool Input Validation.
- Tool Execution.
- Tool Output Validation.
- Error Handling.
- Memory Retrieval.
- Các trường hợp AI không hiểu yêu cầu.
- Các trường hợp AI chọn sai Tool.
- Các trường hợp AI tạo tham số không hợp lệ.

Đối với kết quả AI, sử dụng tiêu chí đánh giá phù hợp thay vì yêu cầu câu trả lời phải giống hệt nhau.

## 11.4. Quy tắc bắt buộc

- Bug đã sửa phải có test tái hiện lỗi khi phù hợp.
- Không xóa test chỉ vì test đang thất bại.
- Không sửa test chỉ để làm cho test pass mà không xác minh yêu cầu.
- Không mock quá mức khiến test không còn kiểm tra logic thực tế.
- Không bỏ qua test thất bại.
- Không tuyên bố test pass nếu chưa thực sự chạy.
- Không thay đổi cấu hình test để che giấu lỗi.

---

# 12. QUY TẮC REFACTOR VÀ BẢO TRÌ

Mục tiêu là giữ code dễ đọc, dễ thay đổi và không tạo ra technical debt không cần thiết.

Bắt buộc:

- Refactor khi phát hiện logic trùng lặp hoặc trách nhiệm không rõ ràng.
- Ưu tiên cải thiện cấu trúc mà không thay đổi hành vi nghiệp vụ ngoài phạm vi yêu cầu.
- Chia nhỏ function hoặc component khi chúng trở nên khó hiểu.
- Đặt tên rõ ràng cho biến, function, class và module.
- Xóa code chết sau khi xác nhận không còn được sử dụng.
- Cập nhật test sau khi refactor.
- Cập nhật tài liệu khi thay đổi kiến trúc hoặc luồng xử lý.
- Giữ tương thích giữa các module.

Không được:

- Refactor toàn bộ dự án khi chỉ cần sửa một chức năng nhỏ.
- Thay đổi nhiều module không liên quan trong cùng một lần sửa nếu không cần thiết.
- Thêm abstraction chỉ để làm code trông có vẻ chuyên nghiệp.
- Giữ lại code cũ không còn sử dụng mà không có lý do.
- Thay đổi hành vi nghiệp vụ ngoài phạm vi được yêu cầu.
- Xóa API hoặc database field mà chưa đánh giá các nơi phụ thuộc.

## 12.1. Quy tắc đánh giá trước khi refactor

Trước khi refactor, phải xác định:

- Vấn đề hiện tại là gì?
- Nguyên nhân nằm ở đâu?
- Phạm vi file/module bị ảnh hưởng?
- Có thể giải quyết bằng thay đổi nhỏ hơn không?
- Có ảnh hưởng API contract không?
- Có ảnh hưởng dữ liệu hiện có không?
- Có test bảo vệ hành vi hiện tại không?

Nếu refactor có phạm vi lớn, phải trình bày kế hoạch và chờ người dùng phê duyệt.

---

# 13. QUY TẮC BẢO MẬT

Bắt buộc:

- Sử dụng `.env` để quản lý cấu hình nhạy cảm.
- Có `.env.example` với giá trị mẫu không nhạy cảm.
- Đưa `.env` vào `.gitignore`.
- Validate dữ liệu đầu vào.
- Không tin tưởng dữ liệu do người dùng hoặc LLM cung cấp.
- Kiểm tra quyền truy cập trước khi thực hiện thao tác dữ liệu.
- Không để lộ thông tin nhạy cảm trong response hoặc log.
- Sử dụng ORM hoặc parameterized query.
- Kiểm soát CORS theo môi trường.
- Có cơ chế xử lý lỗi an toàn.

Không được:

- Commit API Key, token hoặc mật khẩu.
- Lưu mật khẩu dạng plain text.
- Thực thi SQL do LLM tạo ra.
- Thực thi command hoặc code do người dùng cung cấp một cách tùy tiện.
- Để lộ stack trace, secret hoặc thông tin nội bộ.
- Tin tưởng dữ liệu trả về từ bên thứ ba mà không validation.
- Cho phép thao tác dữ liệu quan trọng mà không kiểm tra điều kiện hợp lệ.

---

# 14. QUY TẮC QUẢN LÝ CẤU HÌNH VÀ MÔI TRƯỜNG

Bắt buộc:

- Tách biệt cấu hình giữa Development, Testing và Production.
- Không hardcode URL, API Key, model name hoặc thông tin môi trường.
- Sử dụng biến môi trường hoặc cấu hình tập trung.
- Có file `.env.example`.
- Có hướng dẫn khởi tạo môi trường.
- Có hướng dẫn chạy Frontend và Backend.
- Có hướng dẫn chạy migration.
- Có hướng dẫn chạy test.

Không được:

- Sử dụng cấu hình Production cho môi trường Development một cách tùy tiện.
- Commit dữ liệu cá nhân hoặc dữ liệu nhạy cảm.
- Để các cấu hình quan trọng xuất hiện rải rác trong source code.

---

# 15. QUY TẮC QUẢN LÝ DEPENDENCY

Trước khi thêm thư viện mới, phải đánh giá:

- Thư viện giải quyết vấn đề gì?
- Có thể sử dụng thư viện hiện có không?
- Có cần thiết cho MVP không?
- Có ảnh hưởng đến kiến trúc không?
- Có tương thích với công nghệ đang sử dụng không?
- Có chi phí hoặc giới hạn sử dụng không?
- Có rủi ro bảo mật hoặc bảo trì không?

Bắt buộc:

- Chỉ thêm dependency khi có lý do rõ ràng.
- Sử dụng phiên bản tương thích.
- Cập nhật file quản lý dependency.
- Ghi nhận dependency quan trọng trong tài liệu khi cần thiết.

Không được:

- Cài nhiều thư viện chỉ để giải quyết một vấn đề nhỏ.
- Thêm framework lớn khi chưa được phê duyệt.
- Thay thế thư viện hiện tại mà không đánh giá tác động.
- Tự ý cập nhật hàng loạt dependency trong một thay đổi không liên quan.

---

# 16. QUY TẮC GIT VÀ QUẢN LÝ SOURCE CODE

Bắt buộc:

- Commit có nội dung rõ ràng.
- Mỗi thay đổi nên tập trung vào một mục tiêu.
- Kiểm tra `git status` trước và sau khi thay đổi.
- Kiểm tra diff trước khi hoàn thành.
- Không đưa file build, cache, secret hoặc dữ liệu tạm vào Git.
- Không tự ý thay đổi lịch sử Git.

Quy ước commit:

```text
feat: add finance transaction management
fix: correct budget calculation
refactor: separate finance business logic
test: add transaction service tests
docs: update architecture documentation
chore: update dependencies
```

Không được tự ý:

- `git reset --hard`.
- `git clean -fd`.
- `git push --force`.
- Xóa branch.
- Ghi đè thay đổi của người dùng.
- Commit hoặc push khi chưa được yêu cầu.

Nếu phát hiện thay đổi chưa commit của người dùng, phải giữ nguyên và tránh ghi đè.

---

# 17. QUY TRÌNH BẮT BUỘC KHI NHẬN YÊU CẦU

Mọi yêu cầu phát triển, sửa lỗi hoặc refactor phải tuân thủ quy trình sau.

## Bước 1. Đọc và khảo sát

Trước khi sửa code:

- Đọc CLAUDE.md.
- Kiểm tra cấu trúc thư mục.
- Đọc các file liên quan.
- Xác định module và tầng kiến trúc.
- Tìm các implementation tương tự.
- Kiểm tra các dependency liên quan.
- Kiểm tra trạng thái Git.

Không được giả định cấu trúc dự án khi chưa kiểm tra source code thực tế.

## Bước 2. Phân tích yêu cầu

Xác định:

- Mục tiêu cần đạt.
- Phạm vi thực hiện.
- Luồng nghiệp vụ hiện tại.
- Các module bị ảnh hưởng.
- Các file dự kiến thay đổi.
- Các rủi ro và trường hợp ngoại lệ.
- Những điểm chưa rõ cần hỏi người dùng.

Nếu thiếu thông tin quan trọng, phải hỏi người dùng thay vì tự ý đưa ra giả định có ảnh hưởng lớn.

## Bước 3. Lập kế hoạch

Trình bày kế hoạch trước khi thực hiện với các nội dung:

1. Phân tích hiện trạng.
2. Giải pháp đề xuất.
3. Các file/module cần thay đổi.
4. Luồng xử lý sau khi thay đổi.
5. Các test cần bổ sung hoặc cập nhật.
6. Rủi ro và ảnh hưởng.

Đối với các thay đổi kiến trúc, database, API contract hoặc refactor lớn, bắt buộc chờ người dùng phê duyệt trước khi triển khai.

Đối với bug nhỏ hoặc thay đổi cục bộ, có thể triển khai sau khi đã phân tích rõ phạm vi và không có rủi ro đáng kể.

## Bước 4. Thực hiện

Trong quá trình code:

- Chỉ sửa những phần cần thiết.
- Tuân thủ kiến trúc hiện tại.
- Không tạo code trùng lặp.
- Không thay đổi chức năng ngoài phạm vi.
- Không xóa code hoặc dữ liệu khi chưa xác minh.
- Cập nhật test tương ứng.
- Cập nhật tài liệu nếu có thay đổi cần ghi nhận.

## Bước 5. Kiểm thử và xác minh

Sau khi code:

- Chạy test liên quan.
- Chạy lint/type checking nếu có.
- Kiểm tra lỗi build.
- Kiểm tra API contract nếu bị ảnh hưởng.
- Kiểm tra các luồng nghiệp vụ liên quan.
- Kiểm tra Git diff.
- Xác nhận không có file ngoài phạm vi bị thay đổi.

Nếu không thể chạy test, phải ghi rõ nguyên nhân và những nội dung chưa được xác minh.

## Bước 6. Báo cáo kết quả

Báo cáo ngắn gọn nhưng đầy đủ:

- Đã thực hiện những gì.
- Các file đã thay đổi.
- Những quyết định kỹ thuật quan trọng.
- Kết quả kiểm thử thực tế.
- Các vấn đề còn tồn tại.
- Những việc cần thực hiện tiếp theo.

Không được tuyên bố hoàn thành khi còn lỗi chưa được giải thích.

---

# 18. QUY TẮC TÀI LIỆU HÓA

Tài liệu là một phần của source code và phải được duy trì khi hệ thống thay đổi.

Các tài liệu quan trọng:

```text
docs/
├── architecture/
│   ├── system-overview.md
│   ├── backend-architecture.md
│   ├── frontend-architecture.md
│   ├── ai-architecture.md
│   ├── database-architecture.md
│   └── development-workflow.md
│
├── decisions/
│   └── ADR/                 # NNNN-ten-quyet-dinh.md
│
├── modules/                 # Tạo khi có module nghiệp vụ đầu tiên
│
├── api/
│   └── api-reference.md
│
├── database/
│   └── schema.md            # Schema ĐANG tồn tại trong database
│
├── testing/
│   └── testing-guide.md
│
└── debugging/
    └── debugging-guide.md
```

Bắt buộc:

- Thay đổi kiến trúc phải cập nhật tài liệu kiến trúc.
- Quyết định kỹ thuật quan trọng phải có ADR.
- Thay đổi database phải cập nhật tài liệu schema khi cần thiết.
- Thay đổi API phải cập nhật tài liệu API.
- Thêm module mới phải mô tả trách nhiệm và ranh giới module.
- Hướng dẫn debug phải phản ánh cách hệ thống thực sự hoạt động.

Không được để tài liệu mô tả một kiến trúc khác với source code hiện tại.

---

# 19. QUY TẮC MỞ RỘNG TÍNH NĂNG

Mọi tính năng mới phải được thiết kế để không phá vỡ các module hiện có.

Trước khi thêm tính năng:

1. Xác định module sở hữu nghiệp vụ.
2. Xác định dữ liệu cần lưu trữ.
3. Xác định API contract.
4. Xác định luồng tương tác với AI nếu có.
5. Xác định các module phụ thuộc.
6. Xác định khả năng tái sử dụng.
7. Xác định test cần có.
8. Đánh giá khả năng mở rộng trong tương lai.

Nguyên tắc:

- Ưu tiên mở rộng thông qua module hoặc adapter mới.
- Hạn chế sửa đổi các module không liên quan.
- Không để tính năng mới làm tăng sự phụ thuộc giữa các module.
- Không tạo một module mới nếu chức năng thuộc phạm vi rõ ràng của module hiện tại.
- Không xây dựng trước các tính năng chưa có yêu cầu thực tế.
- Không đánh đổi tính dễ bảo trì để lấy tốc độ triển khai ngắn hạn.

---

# 20. NHỮNG ĐIỀU TUYỆT ĐỐI KHÔNG ĐƯỢC LÀM

Danh sách dưới đây có tính bắt buộc:

1. Không tự ý thay đổi kiến trúc tổng thể.
2. Không tự ý thay đổi stack công nghệ.
3. Không viết code khi chưa khảo sát cấu trúc hiện tại.
4. Không đặt Business Logic trong Router hoặc UI Component.
5. Không cho LLM truy cập database trực tiếp.
6. Không cho LLM tự tính toán dữ liệu tài chính.
7. Không sử dụng `float` để tính toán tiền.
8. Không hardcode secret hoặc cấu hình môi trường.
9. Không bỏ qua lỗi hoặc nuốt exception.
10. Không sửa test chỉ để test pass.
11. Không xóa code, dữ liệu hoặc migration khi chưa đánh giá tác động.
12. Không thêm dependency không cần thiết.
13. Không tạo abstraction hoặc design pattern không có giá trị thực tế.
14. Không tạo circular dependency.
15. Không để module phụ thuộc vào implementation nội bộ của module khác.
16. Không thực hiện refactor lớn khi chưa được phê duyệt.
17. Không ghi đè thay đổi chưa commit của người dùng.
18. Không thực hiện Git destructive command khi chưa được yêu cầu.
19. Không tuyên bố đã kiểm thử nếu chưa chạy kiểm thử.
20. Không tuyên bố hoàn thành khi chưa xác minh kết quả.

---

# 21. CHECKLIST TRƯỚC KHI HOÀN THÀNH MỘT TASK

Claude Code phải tự kiểm tra các mục sau trước khi báo cáo hoàn thành:

## Kiến trúc

- [ ] Code nằm đúng module.
- [ ] Code nằm đúng tầng kiến trúc.
- [ ] Không tạo circular dependency.
- [ ] Không vi phạm ranh giới module (import liên module chỉ qua `public.py`).
- [ ] Không tạo abstraction không cần thiết.

## Chất lượng code

- [ ] Tên biến, function, class rõ ràng.
- [ ] Có Type Hint hoặc TypeScript Type phù hợp.
- [ ] Không có code trùng lặp không cần thiết.
- [ ] Không có code chết mới phát sinh.
- [ ] Không có hardcode cấu hình nhạy cảm.
- [ ] Có xử lý lỗi phù hợp.

## Database và API

- [ ] Schema được validate.
- [ ] Database migration được cập nhật nếu cần.
- [ ] API contract nhất quán.
- [ ] Không có truy vấn hoặc thao tác dữ liệu không an toàn.
- [ ] Không làm mất dữ liệu ngoài dự kiến.

## AI

- [ ] Tool input được validate.
- [ ] Tool output được kiểm tra.
- [ ] LLM không trực tiếp thực thi nghiệp vụ.
- [ ] Có xử lý lỗi khi LLM hoặc Provider thất bại.
- [ ] Có thể truy vết quá trình thực thi.

## Testing

- [ ] Đã bổ sung hoặc cập nhật test phù hợp.
- [ ] Đã chạy test liên quan.
- [ ] Đã kiểm tra lỗi build/lint/type checking khi phù hợp.
- [ ] Toàn bộ lệnh ở mục 23.10 đều đạt.
- [ ] Không bỏ qua test thất bại.
- [ ] Kết quả kiểm thử được báo cáo trung thực.

## Hoàn thiện

- [ ] Đã kiểm tra Git diff.
- [ ] Không thay đổi file ngoài phạm vi không có lý do.
- [ ] Đã cập nhật tài liệu nếu cần.
- [ ] Đã báo cáo các vấn đề còn tồn tại.

---

# 22. NGUYÊN TẮC CUỐI CÙNG

Trong toàn bộ quá trình phát triển AI Personal Assistant, phải ưu tiên theo thứ tự:

1. **Correctness:** Chức năng phải hoạt động đúng yêu cầu.
2. **Maintainability:** Code phải dễ đọc, dễ sửa và dễ bảo trì.
3. **Debuggability:** Có thể truy vết và xác định nguyên nhân lỗi.
4. **Extensibility:** Có thể bổ sung tính năng mà không phá vỡ hệ thống.
5. **Testability:** Có thể kiểm thử độc lập và tự động.
6. **Performance:** Tối ưu hiệu năng khi có cơ sở và nhu cầu thực tế.
7. **Simplicity:** Ưu tiên giải pháp đơn giản, dễ hiểu, tránh overengineering.

**Không hy sinh tính đúng đắn, khả năng bảo trì và khả năng debug để đổi lấy việc viết code nhanh hơn.**

Mọi thay đổi phải hướng đến một hệ thống có cấu trúc rõ ràng, trách nhiệm phân tách hợp lý, có thể kiểm thử, dễ mở rộng và dễ tiếp tục phát triển trong dài hạn.
---

# 23. QUY ƯỚC TRIỂN KHAI CỦA CODEBASE

Mục này ghi lại các quy ước cụ thể đã được phê duyệt và đang được áp dụng trong source code. Code mới phải theo đúng các quy ước này. Lý do của từng quyết định nằm trong `docs/decisions/ADR/`.

Nếu cần làm khác một quy ước ở đây, phải trình bày lý do, chờ người dùng phê duyệt, rồi cập nhật mục này và ADR liên quan trong cùng thay đổi.

## 23.1. Cấu trúc repository

```text
A.T.L.A.S/
├── CLAUDE.md
├── README.md
├── backend/
│   ├── pyproject.toml, uv.lock, alembic.ini, .env.example
│   ├── alembic/                 # env.py, versions/
│   ├── app/
│   │   ├── __main__.py          # `python -m app`: chạy server theo Settings
│   │   ├── main.py              # create_app()
│   │   ├── bootstrap.py         # Composition root: nơi DUY NHẤT biết mọi module
│   │   ├── api/v1.py            # Gom router của các module dưới /api/v1
│   │   ├── core/                # config, logging, middleware, exceptions, error_handlers
│   │   ├── shared/              # Contract dùng chung (tools.py)
│   │   ├── infrastructure/      # database/: base.py, session.py, models.py
│   │   └── modules/<module>/
│   └── tests/                   # Phản chiếu cấu trúc app/
├── frontend/
│   ├── package.json, vite.config.ts, .env.example
│   └── src/                     # app, pages, features, components, hooks, services, config, types, utils
└── docs/
```

- Không có `.env.example` ở thư mục gốc. Backend và Frontend có file riêng.
- Không tạo thư mục hoặc file rỗng. File chỉ xuất hiện khi có nội dung thực.

## 23.2. Module Backend

Mỗi module nằm trong `backend/app/modules/<module>/` và chỉ chứa các file nó thực sự cần:

| File | Nội dung |
|---|---|
| `public.py` | Public interface DUY NHẤT của module |
| `router.py` | Endpoint FastAPI |
| `schemas.py` | Pydantic request/response và DTO trao đổi giữa module |
| `service.py` | Use case và quy tắc nghiệp vụ |
| `repository.py` | Truy vấn SQLAlchemy |
| `models.py` | ORM model |
| `dependencies.py` | Hàm factory cho FastAPI `Depends` |
| `exceptions.py` | Lỗi riêng của module, kế thừa `AppError` |
| `tools.py` | Tool cung cấp cho AI (nếu có) |

Quy tắc phụ thuộc (được kiểm tra bởi `tests/architecture/test_module_boundaries.py`):

- Module khác chỉ import `app.modules.<module>.public`.
- `app.modules.ai` không import `finance`, `travel`, `food`, `dashboard`.
- `app.core`, `app.shared`, `app.infrastructure` không import `app.modules`. Ngoại lệ duy nhất: `infrastructure/database/models.py` import `models` của mọi module.
- `service.py` không import `fastapi` hoặc `starlette`.
- Hướng phụ thuộc hiện tại: `health` → `ai`; `ai` → `memory`, `users`. Không tạo chiều ngược lại.

Khi một file vượt quá khoảng 300 dòng hoặc chứa nhiều nhóm nghiệp vụ, tách thành package cùng tên.

## 23.3. Tầng xử lý Backend

- Service là class Python thuần, nhận dependency qua constructor. Không dùng DI container.
- **Service sở hữu transaction** và gọi `commit()`. Repository chỉ `add`, `flush`, `execute`; repository không `commit()`.
- Mỗi request dùng một `AsyncSession` từ dependency `get_session`.
- Service ném exception kế thừa `AppError` (`app/core/exceptions.py`). Router không có `try/except`.
- Chọn lớp cha theo loại lỗi: `ValidationFailedError` (422), `NotFoundError` (404), `ConflictError` (409), `BusinessRuleError` (422), `ExternalServiceError` (502), `ExternalServiceTimeoutError` (504), `ExternalServiceUnavailableError` (503).
- Lỗi của module đặt `code` dạng `snake_case` và `message` tiếng Việt hiển thị được cho người dùng.
- Adapter bắt lỗi của thư viện và ném lại bằng `raise ... from error`.
- Dữ liệu trả ra khỏi module là Pydantic model hoặc kiểu nguyên thủy, không phải ORM model.
- Logger: `logger = logging.getLogger(__name__)`. Ngữ cảnh truyền qua `extra={...}`, không nối vào chuỗi thông điệp. Thông điệp log viết bằng tiếng Anh.
- Đối tượng sống suốt vòng đời ứng dụng được tạo trong `lifespan` và lưu ở `app.state`.

## 23.4. Database

- Khóa chính: `UuidPrimaryKeyMixin` (UUID sinh ở ứng dụng).
- Thời gian: kiểu `UtcDateTime`, luôn là `datetime` có timezone. Dùng `TimestampMixin` hoặc `CreatedAtMixin`. Giá trị `datetime` không có timezone bị từ chối.
- Giá trị liệt kê: `StrEnum` lưu dạng chuỗi (`native_enum=False`). Không dùng kiểu `ENUM` của database.
- Mọi khóa ngoại khai báo `ondelete` tường minh. Mặc định `RESTRICT`. `CASCADE` chỉ dùng cho quan hệ thành phần.
- Mọi `relationship()` đặt `lazy="raise"`. Dữ liệu liên quan được nạp tường minh bằng `selectinload` hoặc `joinedload`.
- Không khai báo `relationship()` giữa model của hai module. Khóa ngoại liên module chỉ là cột ID.
- Mọi bảng dữ liệu cá nhân có cột `user_id` trỏ tới `users.id`.
- Tên ràng buộc do naming convention trong `infrastructure/database/base.py` sinh ra. Không đặt tên thủ công trái quy ước.
- Không dùng SQL thô và không dùng `Base.metadata.create_all()` trong code ứng dụng.

Migration:

- Sinh bằng `uv run alembic revision --autogenerate -m "<mô tả>"`, sau đó **đọc và chỉnh** file trước khi áp dụng.
- File migration không import code ứng dụng.
- Mỗi migration có `downgrade()` hoạt động được. Migration làm mất dữ liệu phải được nêu rõ và chờ phê duyệt.
- Model mới phải được import trong `app/infrastructure/database/models.py`.
- Sau khi đổi schema: cập nhật `docs/database/schema.md`.

## 23.5. API

- Mọi endpoint nằm dưới `/api/v1`. Router của module được thêm vào `app/api/v1.py`.
- Mọi lỗi trả cùng một cấu trúc:

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

- Danh sách có khả năng tăng trưởng trả dạng `{"items": [], "total": 0, "limit": 20, "offset": 0}`.
- Mọi response có header `X-Request-ID`.
- Sau khi thêm hoặc đổi endpoint: cập nhật `docs/api/api-reference.md` và kiểu dữ liệu tương ứng ở Frontend.

## 23.6. AI Core

- Tool contract nằm tại `app/shared/tools.py`: `Tool`, `ToolSpec`, `ToolContext`, `ToolResult`.
- Tool của một module được định nghĩa trong `modules/<module>/tools.py` và đăng ký tại `build_tool_registry()` trong `app/bootstrap.py`.
- Tên Tool có dạng `<domain>_<action>`, chỉ gồm chữ thường, số và dấu gạch dưới. `domain` trùng với intent chọn Tool đó.
- Mỗi Tool có `input_model` và `output_model` là Pydantic model. JSON Schema gửi cho model được sinh từ `input_model`; không viết schema bằng tay.
- `user_id` và `conversation_id` luôn lấy từ `ToolContext`. Không bao giờ nhận chúng từ tham số do model tạo.
- Tool không chứa quy tắc nghiệp vụ. Tool gọi service của chính module đó.
- Tool làm thay đổi dữ liệu khai báo `effect=ToolEffect.WRITE`.
- `ToolExecutor` biến mọi thất bại của Tool thành `ToolResult`. Tool ném `AppError` cho lỗi nghiệp vụ; không tự bắt exception để trả chuỗi lỗi.
- Mọi lời gọi model đi qua interface `LLMProvider`. Chỉ code trong `modules/ai/providers/` được gửi request tới dịch vụ LLM.
- Nhà cung cấp mới: thêm một adapter trong `modules/ai/providers/` và một nhánh trong `factory.py`.
- Tin nhắn của người dùng được lưu trước khi gọi model.
- Giới hạn vòng Tool, timeout và kích thước ngữ cảnh lấy từ `Settings`, không hardcode.
- Dữ liệu ghi vào AI execution log phải đi qua `redact()`.

## 23.7. Frontend

- Import nội bộ dùng alias `@/` (trỏ tới `src/`).
- Hướng import: `app` → `pages` → `features` → `components` / `hooks` / `services` → `utils` / `types` / `config`. Không import ngược. Feature không import file nội bộ của feature khác.
- Một feature nằm trong `src/features/<feature>/` gồm `api.ts`, `types.ts`, `hooks/`, `components/`.
- Chỉ `features/<feature>/api.ts` gọi `apiClient`. Component và hook không import Axios.
- Chỉ `src/config/env.ts` đọc `import.meta.env`.
- Mọi lỗi từ tầng API là `ApiError` (`src/services/api/errors.ts`). Component hiển thị `error.message` và `error.requestId`.
- Luồng tải dữ liệu dùng `useAsyncData` và hiển thị đủ các trạng thái Loading, Empty, Error, Success.
- Kiểu dữ liệu trao đổi với Backend đặt trong `features/<feature>/types.ts`, kèm ghi chú schema Backend tương ứng.
- Lỗi bất ngờ được báo qua `reportError`, không gọi `console.error` trực tiếp.
- Không dùng `any`. Không dùng `enum` và parameter property của TypeScript (`erasableSyntaxOnly`).
- Văn bản giao diện viết bằng tiếng Việt.
- File test đặt cạnh file nguồn: `X.tsx` và `X.test.tsx`.

## 23.8. Cấu hình và địa chỉ chạy

| Thành phần | Địa chỉ mặc định | Biến cấu hình |
|---|---|---|
| Backend API | `http://127.0.0.1:8710` | `API_HOST`, `API_PORT` (`backend/.env`) |
| Frontend dev server | `http://localhost:5710` | `VITE_DEV_SERVER_PORT` (`frontend/.env`) |
| Ollama | `http://localhost:11434` | `OLLAMA_BASE_URL` (`backend/.env`) |

- Dự án dùng cổng **8710** và **5710**. Không dùng lại 8000 và 5173, vì các cổng đó trùng với dự án khác trên cùng máy.
- `VITE_API_BASE_URL` phải khớp `API_PORT`. `CORS_ALLOWED_ORIGINS` phải khớp cổng Frontend. Khi đổi một giá trị, đổi cả giá trị đi cùng và cập nhật `README.md`.
- Backend chỉ lắng nghe `127.0.0.1` cho đến khi có authentication.
- Biến cấu hình Backend mới phải được thêm đồng thời vào: class `Settings` (`app/core/config.py`), `backend/.env.example`, bảng cấu hình trong `docs/architecture/backend-architecture.md`, và test trong `tests/core/test_config.py`.
- Không đọc `os.environ` ngoài `app/core/config.py`.

## 23.9. Kiểm thử

- Test không cần Ollama, không cần mạng, không đọc `.env` của người phát triển và không dùng `backend/data/app.db`.
- Test Backend dùng fixture trong `tests/conftest.py`: `database_path`, `settings`, `app`, `client`, `session`. Database của test được tạo bằng migration thật.
- Repository và ràng buộc database được kiểm thử trên SQLite thật. Không mock SQLAlchemy.
- Test AI dùng `MockLLMProvider` và các Tool mẫu trong `tests/ai_support.py`. Test kiểm tra hành vi (Tool nào chạy, tham số nào, dữ liệu nào được lưu), không so sánh nguyên văn câu trả lời.
- Adapter dịch vụ ngoài được kiểm thử bằng `httpx.MockTransport`.
- Test Frontend không gọi Backend thật: dùng `vi.mock` cho `api.ts` của feature, hoặc truyền `adapter` giả vào `createApiClient`.
- Tên test mô tả hành vi được kiểm tra, ví dụ `test_tool_loop_stops_at_the_iteration_limit`.

## 23.10. Lệnh và cổng chất lượng

Chạy Backend trong `backend/`:

| Mục đích | Lệnh |
|---|---|
| Cài dependency | `uv sync` |
| Áp dụng migration | `uv run alembic upgrade head` |
| Chạy server | `uv run python -m app` |
| Thêm dependency | `uv add <gói>` hoặc `uv add --dev <gói>` |

Chạy Frontend trong `frontend/`:

| Mục đích | Lệnh |
|---|---|
| Cài dependency | `npm install` |
| Chạy dev server | `npm run dev` |

**Cổng chất lượng.** Một task chỉ được báo hoàn thành khi mọi lệnh sau đều đạt:

```bash
# backend/
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run alembic check

# frontend/
npm run test
npm run lint
npm run build
```

Chỉ cần chạy nhóm lệnh của phần đã thay đổi. Báo cáo phải nêu số test đạt và thất bại lấy từ kết quả chạy thực tế.

## 23.11. Quy trình cho các thay đổi thường gặp

Thêm module nghiệp vụ:

1. Tạo `app/modules/<module>/` theo mục 23.2.
2. Import `models` của module trong `app/infrastructure/database/models.py`.
3. Tạo và rà soát migration.
4. Thêm router vào `app/api/v1.py`.
5. Viết test trong `tests/modules/<module>/`.
6. Cập nhật `docs/database/schema.md`, `docs/api/api-reference.md` và mục 3.2 của file này.

Thêm Tool cho AI:

1. Định nghĩa Tool trong `modules/<module>/tools.py` theo mục 23.6.
2. Đăng ký tại `build_tool_registry()` trong `app/bootstrap.py`.
3. Viết test cho: input hợp lệ, input không hợp lệ, lỗi nghiệp vụ, và một lượt chat dùng Tool qua `MockLLMProvider`.

Thêm màn hình Frontend:

1. Tạo `src/features/<feature>/` theo mục 23.7.
2. Tạo trang trong `src/pages/` và thêm route vào `src/app/router.tsx`.
3. Viết test cho component, hook và hàm trong `api.ts`.

## 23.12. Lưu ý môi trường

- Vitest báo "failed to find the current suite" khi terminal đứng ở đường dẫn có ký tự ổ đĩa viết thường (`c:\...`). Chạy từ `C:\...`.
- Repository hiện nằm trong thư mục OneDrive. Lỗi khóa file hoặc `database is locked` cần được xem xét theo nguyên nhân này trước.
- Khi chuyển hướng log Backend vào file trên Windows, đặt `PYTHONUTF8=1` để chữ tiếng Việt không bị thay bằng mã escape.
- Chi tiết: `docs/debugging/debugging-guide.md`.
