# AI Personal Assistant

Trợ lý cá nhân dùng AI, chạy cục bộ, kết hợp giao diện Chat và Dashboard.

Trạng thái hiện tại: **nền tảng kỹ thuật**. Hệ thống có khung Backend, Frontend, database và hạ tầng AI. Các nghiệp vụ Finance, Travel, Food Discovery và Dashboard chưa được triển khai.

| Thành phần | Công nghệ |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Axios |
| Database | SQLite |
| AI | Ollama qua Provider Adapter |
| Test | Pytest; Vitest + React Testing Library |

## Địa chỉ khi chạy

| Thành phần | Địa chỉ | Cấu hình tại |
| --- | --- | --- |
| Frontend | <http://localhost:5710> | `VITE_DEV_SERVER_PORT` trong `frontend/.env` |
| Backend API | <http://127.0.0.1:8710/api/v1> | `API_HOST`, `API_PORT` trong `backend/.env` |
| Tài liệu API tương tác | <http://127.0.0.1:8710/docs> | Chỉ có khi `APP_ENV` khác `production` |
| Health check | <http://127.0.0.1:8710/api/v1/health> | |

Dự án dùng cổng **8710** và **5710** thay cho 8000 và 5173 để không trùng với dự án khác trên cùng máy.

## Yêu cầu

| Công cụ | Phiên bản | Kiểm tra |
| --- | --- | --- |
| Python | 3.13 trở lên (đã kiểm thử với 3.14) | `python --version` |
| [uv](https://docs.astral.sh/uv/) | 0.11 trở lên | `uv --version` |
| Node.js | 24 | `node --version` |
| npm | 11 | `npm --version` |
| [Ollama](https://ollama.com) | Tùy chọn. Chỉ cần khi dùng Chat với model thật | `ollama --version` |

## Chạy lần đầu

### Bước 1. Lấy mã nguồn

```bash
git clone <repository-url>
cd A.T.L.A.S
```

Không nên đặt repository trong thư mục được OneDrive, Dropbox hoặc công cụ tương tự đồng bộ. Xem [hướng dẫn debug](docs/debugging/debugging-guide.md#repository-nằm-trong-thư-mục-đồng-bộ).

### Bước 2. Cài đặt Backend

Mở terminal thứ nhất.

```bash
cd backend
uv sync
```

`uv sync` tạo môi trường ảo `.venv` và cài đúng phiên bản dependency trong `uv.lock`.

### Bước 3. Cấu hình Backend

Tạo file `.env` từ file mẫu.

```bash
# Git Bash, macOS, Linux
cp .env.example .env
```

```powershell
# PowerShell
Copy-Item .env.example .env
```

Giá trị mặc định đủ để chạy. Ý nghĩa từng biến có trong `.env.example`.

### Bước 4. Khởi tạo database

```bash
uv run alembic upgrade head
```

Lệnh này tạo file `backend/data/app.db`, tạo các bảng và người dùng mặc định.

### Bước 5. Chạy Backend

```bash
uv run python -m app
```

Kiểm tra: mở <http://127.0.0.1:8710/api/v1/health>. Kết quả mong đợi có `"status":"ok"` và `"database":"ok"`.

Giữ terminal này mở. Nhấn `Ctrl+C` để dừng server.

### Bước 6. Cài đặt và cấu hình Frontend

Mở terminal thứ hai.

```bash
cd frontend
npm install
```

```bash
# Git Bash, macOS, Linux
cp .env.example .env
```

```powershell
# PowerShell
Copy-Item .env.example .env
```

### Bước 7. Chạy Frontend

```bash
npm run dev
```

Kiểm tra: mở <http://localhost:5710>. Trang Tổng quan hiển thị trạng thái Backend, database và AI. Trang Trợ lý AI ở <http://localhost:5710/chat>.

### Bước 8. Cấu hình AI (tùy chọn)

Backend chạy được mà không cần Ollama. Khi đó trang chủ báo AI "Chưa sẵn sàng" và endpoint chat trả lỗi `llm_not_configured` hoặc `llm_unavailable`.

Để dùng model thật:

1. Cài Ollama và tải một model hỗ trợ tool calling: `ollama pull <tên-model>`.
2. Đặt `OLLAMA_MODEL=<tên-model>` trong `backend/.env`.
3. Khởi động lại Backend.

Để thử luồng chat mà không cần Ollama, đặt `LLM_PROVIDER=mock` trong `backend/.env`. Provider này trả một câu trả lời cố định.

Gửi thử một tin nhắn: mở <http://127.0.0.1:8710/docs>, chọn `POST /api/v1/chat`, nhấn "Try it out".

### Bước 9. Dữ liệu du lịch (tùy chọn)

Bản đồ, tìm địa điểm, thời tiết và quãng đường dùng dịch vụ miễn phí, không cần khóa: OpenStreetMap, Open-Meteo, OSRM. Máy chạy Backend và trình duyệt cần truy cập Internet.

- Nên đặt `OSM_CONTACT` (email hoặc trang web của bạn) trong `backend/.env`. Chính sách của Nominatim yêu cầu ứng dụng tự giới thiệu.
- Giá vé máy bay cần khóa SerpApi (gói miễn phí giới hạn số lượt tìm mỗi tháng). Đặt `SERPAPI_API_KEY` trong `backend/.env`. Không có khóa, Atlas đưa liên kết Google Flights.
- Tàu hỏa và xe khách: Atlas đưa quãng đường và liên kết dsvn.vn, Vexere. Atlas không có giờ chạy và giá vé.
- Ẩm thực tìm quán qua Photon (OpenStreetMap), dự phòng bằng Overpass API, không cần khóa. Dịch vụ công khai đôi khi quá tải và trả lỗi `overpass_error`; khi đó Atlas báo "Chưa tìm được quán" và có thể thử lại sau, hoặc đặt `OVERPASS_BASE_URL` sang một máy chủ khác.

## Chạy các lần sau

```bash
# Terminal 1
cd backend
uv run python -m app

# Terminal 2
cd frontend
npm run dev
```

Sau khi lấy code mới về, chạy thêm trước khi khởi động:

```bash
# backend/
uv sync
uv run alembic upgrade head

# frontend/
npm install
```

## Đổi địa chỉ

| Muốn đổi | Sửa |
| --- | --- |
| Cổng Backend | `API_PORT` trong `backend/.env`, và `VITE_API_BASE_URL` trong `frontend/.env` |
| Cổng Frontend | `VITE_DEV_SERVER_PORT` trong `frontend/.env`, và `CORS_ALLOWED_ORIGINS` trong `backend/.env` |

Hai giá trị trong mỗi dòng phải khớp nhau. Khởi động lại cả hai server sau khi sửa.

Frontend không tự chuyển sang cổng khác khi cổng đang bị chiếm. Lý do: Backend chỉ chấp nhận request từ origin đã khai báo trong `CORS_ALLOWED_ORIGINS`.

## Chạy test

```bash
# Backend (trong backend/)
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests

# Frontend (trong frontend/)
npm run test
npm run lint
npm run build
```

Test không cần Ollama, không cần mạng và không dùng database phát triển. Chi tiết: [hướng dẫn kiểm thử](docs/testing/testing-guide.md).

## Sự cố thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Trang chủ báo "Không kết nối được tới máy chủ" | Backend chưa chạy, hoặc `VITE_API_BASE_URL` không khớp `API_PORT` |
| Lỗi CORS trong console trình duyệt | Origin của Frontend chưa có trong `CORS_ALLOWED_ORIGINS` |
| `Port 5710 is already in use` | Dừng tiến trình đang giữ cổng, hoặc đổi cổng theo mục "Đổi địa chỉ" |
| API trả `default_user_missing` | Chưa chạy `uv run alembic upgrade head` |
| Chat trả `llm_not_configured` | Chưa đặt `OLLAMA_MODEL` |
| Chat trả `llm_unavailable` | Ollama chưa chạy |
| Không tìm được địa điểm, bản đồ trống | Atlas tự chuyển sang nguồn dự phòng (Photon cho địa điểm và quán, tile.openstreetmap.de cho bản đồ) khi `openstreetmap.org` bị chặn. Nếu vẫn lỗi, mạng đang chặn cả các nguồn này: đổi DNS hoặc đặt `PHOTON_BASE_URL`, `VITE_MAP_FALLBACK_TILE_URL` sang máy chủ khác |
| Vitest báo "failed to find the current suite" | Chuyển vào thư mục bằng ký tự ổ đĩa viết hoa: `cd C:\...\frontend` |

Chi tiết hơn: [hướng dẫn debug](docs/debugging/debugging-guide.md).

## Cấu trúc repository

```text
A.T.L.A.S/
├── CLAUDE.md        # Quy tắc phát triển bắt buộc
├── backend/         # FastAPI: app/, alembic/, tests/
├── frontend/        # React: src/
└── docs/
    ├── architecture/   # Kiến trúc hệ thống
    ├── decisions/ADR/  # Quyết định kỹ thuật
    ├── database/       # Schema hiện tại
    ├── api/            # Tài liệu API
    ├── testing/        # Hướng dẫn kiểm thử
    ├── debugging/      # Hướng dẫn debug
    └── design/         # Design system
```

## Tài liệu

| Chủ đề | Tài liệu |
| --- | --- |
| Quy tắc phát triển | [CLAUDE.md](CLAUDE.md) |
| Tổng quan kiến trúc | [system-overview.md](docs/architecture/system-overview.md) |
| Backend | [backend-architecture.md](docs/architecture/backend-architecture.md), [backend/README.md](backend/README.md) |
| Frontend | [frontend-architecture.md](docs/architecture/frontend-architecture.md), [frontend/README.md](frontend/README.md) |
| Giao diện | [design-system.md](docs/design/design-system.md) |
| AI | [ai-architecture.md](docs/architecture/ai-architecture.md) |
| Database | [database-architecture.md](docs/architecture/database-architecture.md), [schema.md](docs/database/schema.md) |
| API | [api-reference.md](docs/api/api-reference.md) |
| Quy trình phát triển | [development-workflow.md](docs/architecture/development-workflow.md) |
| Kiểm thử | [testing-guide.md](docs/testing/testing-guide.md) |
| Debug | [debugging-guide.md](docs/debugging/debugging-guide.md) |
| Quyết định kỹ thuật | [docs/decisions/ADR/](docs/decisions/ADR/) |

## Giới hạn hiện tại

- Chưa có authentication. Backend chỉ được chạy trên máy cá nhân và không được mở ra mạng.
- Câu trả lời của trợ lý hiện ra khi đã soạn xong, chưa hiện dần từng chữ (chưa có streaming).
- Trợ lý có Tool của Tài chính và Du lịch. Mọi thay đổi dữ liệu do trợ lý đề xuất chỉ được lưu khi người dùng bấm xác nhận.
- Du lịch chưa có giờ chạy và giá vé tàu, xe (chỉ có liên kết). Giá vé máy bay cần khóa SerpApi.
- Adapter Ollama chưa được kiểm thử với Ollama thật.
