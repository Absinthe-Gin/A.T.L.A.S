# Design system

Hệ thống thiết kế của giao diện Atlas. Tài liệu mô tả đúng những gì đang có trong `frontend/src`.

## 1. Định hướng: sổ tay cá nhân

Atlas là cuốn sổ tay cho đời sống hằng ngày. Giao diện ấm áp và thân thiện: giấy kem có dòng kẻ, chữ mực đậm, nút màu cam ấm, và mỗi phân hệ là một tờ giấy nhớ có màu riêng.

Hướng này tham khảo ngôn ngữ UI/UX của [EduMind](https://www.edumindvn.com/) ở các điểm:

- giấy có dòng kẻ;
- tiêu đề weight 800 với nét bút dạ quang;
- nút cam có bóng ngả màu và viền sáng phía trên;
- giấy nhớ pastel hơi nghiêng có băng dính;
- thẻ được dán bằng băng dính;
- nhãn dạng viên thuốc.

Không lấy logo, tên, câu chữ, ảnh minh họa hay bố cục của EduMind.

Không dùng:

- Emoji làm icon. Icon là SVG trong `components/icons`.
- Nhãn nhỏ viết hoa phía trên tiêu đề.
- Chữ đổ màu gradient.
- Dấu `·` để nối thông tin.
- Vạch màu dày hơn 1px ở cạnh trái hoặc phải của khối nội dung.
- Font mono cho nhãn. Mono chỉ dùng cho mã định danh: mã yêu cầu, mã hội thoại, tên Tool, giá trị intent.

## 2. Design tokens

Định nghĩa tại `frontend/src/index.css`. Component chỉ dùng utility ngữ nghĩa sinh từ token. Không dùng màu palette Tailwind hoặc mã hex trong component.

### 2.1. Màu nền và chữ

| Token | Vai trò | Sáng | Tối (sổ tay dưới đèn) |
| --- | --- | --- | --- |
| `bg` | Giấy: nền trang, có dòng kẻ mỗi 32px (`--rule`) | `#fff9f1` | `#1b1712` |
| `chrome` | Lề sổ: sidebar, thanh trên cùng, thanh tiêu đề chat | `#fff4e7` | `#16130f` |
| `surface` | Giấy trắng nổi: thẻ trạng thái, ô nhập, câu trả lời của AI, mục điều hướng đang chọn | `#ffffff` | `#25201a` |
| `surface-2` | Hover, skeleton, nút disabled | `#fdf1e3` | `#2f2820` |
| `border` / `border-strong` | Đường kẻ, viền control | `#f0e2d0` / `#e2cdb4` | `#3a3128` / `#52463a` |
| `fg` | Mực | `#1c2238` | `#f4ede3` |
| `fg-muted` | Chữ phụ | `#4a5068` | `#c8bdb0` |
| `fg-subtle` | Chú thích | `#646a7e` | `#a3988b` |

### 2.2. Màu hành động và trạng thái

| Token | Vai trò | Sáng | Tối |
| --- | --- | --- | --- |
| `primary` | Cam dạng nét: link, viền focus | `#b23a0a` | `#fb9a5c` |
| `action` | Nền nút chính và bong bóng tin nhắn của người dùng. Gradient ngắn `#cc4a0e` → `#b93c0a`, hover `#a8360a`, chữ trắng ≥ 4.6:1 | như nhau | như nhau |
| `marker` | Bút dạ quang dưới lời chào, nền vùng chữ được chọn | `#fcd34d` | vàng 32% |
| `accent` | Xanh dừa cạn: mọi thứ AI nói hoặc làm | `#3b5bdb` | `#9db2ff` |
| `success` / `warning` / `danger` | Trạng thái | `#1f7a45` / `#9a5300` / `#b42318` | `#6fd394` / `#f4b85a` / `#ff8f80` |

Mỗi màu trạng thái có biến thể `-soft` làm nền nhãn.

### 2.3. Màu giấy nhớ

Mỗi phân hệ có một màu, khai báo ở `note` trong `features/modules/catalog.tsx`:

| Màu | Giấy (sáng) | Mực (sáng) | Phân hệ |
| --- | --- | --- | --- |
| `blue` | `#e1e9ff` | `#2f4ab8` | Trợ lý AI |
| `green` | `#ddf2dc` | `#23703a` | Tài chính |
| `yellow` | `#fff4c2` | `#8a5a00` | Du lịch, Tổng quan |
| `peach` | `#ffe6d5` | `#a2410f` | Ẩm thực |
| `pink` | `#fde2e6` | `#a8294a` | Ghi nhớ |

Ở giao diện tối, giấy nhớ là phiên bản trầm của cùng màu, mực sáng hơn. Class lấy từ `NOTE_PAPER` và `NOTE_INK` trong `components/ui/noteColors.ts`, không ghép tên class động (Tailwind không sinh được class ghép lúc chạy).

Băng dính (`--tape`) là băng giấy vàng nhạt trong suốt ở giao diện sáng, để thấy được cả trên giấy kem.

### 2.4. Typography

Một họ font: **Be Vietnam Pro**, thiết kế cho tiếng Việt, giữ dấu rõ ở weight 800.

| Cấp | Class |
| --- | --- |
| Lời chào Tổng quan | `text-5xl sm:text-6xl font-extrabold tracking-tight`, có `.marker` |
| Tiêu đề trang (h1) | `text-4xl font-extrabold tracking-tight` |
| Tiêu đề khối (h2) | `text-3xl font-extrabold tracking-tight` |
| Tiêu đề giấy nhớ, thẻ (h3) | `text-lg font-extrabold` |
| Đoạn dẫn | `text-lg text-fg-muted` |
| Nội dung tin nhắn | `text-[0.9375rem]` |
| Nhãn, chú thích | `text-sm` / `text-xs` |

### 2.5. Hình khối và độ nổi

| Token | Giá trị | Dùng cho |
| --- | --- | --- |
| `rounded-note` | 6px | Giấy nhớ, thẻ dán |
| `rounded-control` | 10px | Nút, mục điều hướng |
| `rounded-card` | 14px | Khung soạn tin, hộp thông tin |
| `rounded-bubble` | 18px | Bong bóng tin nhắn |
| `rounded-full` | | Nhãn trạng thái, icon tròn |

| Bóng | Dùng cho |
| --- | --- |
| `shadow-raise` | Control nổi, mục đang chọn, câu trả lời của AI |
| `shadow-lift` | Giấy nhớ và thẻ dán: bóng dài, ngả nâu |
| `.btn-action` | Nút chính: viền sáng phía trên và bóng cam phía dưới |

## 3. Component dùng chung

| Component | File | Ghi chú |
| --- | --- | --- |
| `Button`, `buttonClasses` | `ui/Button.tsx`, `ui/buttonClasses.ts` | `primary` (cam, `.btn-action`), `secondary` (giấy trắng, viền), `ghost`, `danger`; cỡ `sm` 40px, `md` 44px |
| `StickyNote` | `ui/StickyNote.tsx` | `color`, `tilt` (độ nghiêng, giữ trong khoảng ±1°), `interactive` (thẳng lại và nhấc lên khi hover/focus), `tape` (`center`, `corners`, `none`) |
| `NOTE_PAPER`, `NOTE_INK` | `ui/noteColors.ts` | Class màu giấy và mực theo màu giấy nhớ |
| `IconButton` | `ui/IconButton.tsx` | 40×40px; `label` bắt buộc |
| `Badge`, `InlineAlert`, `EmptyState`, `Card`, `Spinner` | `ui/` | Như trước |
| `PageHeader`, `PageContainer` | `PageHeader.tsx` | Tiêu đề trang đậm; khung `max-w-6xl` |
| `ModuleNotes` | `features/modules/components/ModuleNotes.tsx` | Bảng giấy nhớ các phân hệ |

Trạng thái của nút:

| Trạng thái | Cách hiển thị |
| --- | --- |
| Hover | Nút chính đậm hơn; nút phụ chuyển `surface-2`, viền ngả cam |
| Focus bàn phím | Viền `ring` 2px, cách 2px |
| Nhấn | Lún 1px, mất bóng |
| Disabled | Nền `surface-2`, chữ `fg-subtle`, không bóng, không gradient |
| Loading | Spinner thay icon, khóa nút, `aria-busy` |

Nút điều hướng sang trang khác (ví dụ "Trò chuyện với Atlas" ở Tổng quan) có icon mũi tên SVG ở cuối.

## 4. Màn hình

| Route | Bố cục |
| --- | --- |
| `/` | Nhãn trạng thái dạng viên thuốc; lời chào lớn có bút dạ quang; đoạn giới thiệu; nút "Trò chuyện với Atlas" và "Xem các phân hệ". Bên phải là thẻ trạng thái hệ thống được dán băng dính. Bên dưới là bảng giấy nhớ các phân hệ |
| `/chat` | Thanh tiêu đề trên nền lề sổ; tin nhắn của người dùng là bong bóng cam; câu trả lời của Atlas là thẻ trắng có tên và biểu tượng màu xanh; khung soạn tin trắng, nút gửi cam |
| `/finance`, `/travel`, `/food`, `/memory` | Tiêu đề trang; bên trái giải thích phân hệ chưa triển khai và hai nút; bên phải danh sách "Chức năng dự kiến" viết trên giấy nhớ màu của phân hệ, mỗi mục có ô vuông chưa đánh dấu |

Sidebar là lề sổ (`chrome`). Trang hiện tại là tờ giấy trắng nổi, icon mang màu của phân hệ. Dưới 1024px, sidebar thành thanh trên cùng với menu thu gọn.

## 5. Chuyển động

Toàn bộ bằng CSS. Đường cong `ease-out` = `cubic-bezier(0.16, 1, 0.3, 1)`.

| Chuyển động | Ý nghĩa | Thời lượng |
| --- | --- | --- |
| Giấy nhớ thẳng lại và nhấc lên khi hover hoặc focus | Tờ này là liên kết, đang được chọn | 200ms |
| Đổi trang: hiện dần và trồi 6px | Đã sang nơi khác | 220ms |
| Gửi tin nhắn: bong bóng nở ra từ góc | Tin đã đi | 220ms |
| Câu trả lời, cảnh báo: hiện dần và trồi 8px | Có nội dung mới | 260ms |
| Ba chấm "đang soạn" | Trợ lý đang làm việc | lặp 1.1s |
| Nhấn nút: lún 1px | Đã nhận cú nhấn | 150ms |
| Icon làm mới xoay | Đang kiểm tra | đến khi xong |
| Đổi giao diện sáng/tối: màu chuyển dần, icon xoay vào | Không nháy | 240ms |
| Menu mobile mở và đóng theo chiều cao | Menu ở đâu | 250ms |

Khi bật `prefers-reduced-motion`, `--motion-distance` về 0: bỏ dịch chuyển, phóng to và xoay; giữ hiệu ứng mờ dần và đổi màu.

## 6. Viết nội dung

- Câu ngắn, chủ động, thân thiện; viết hoa chữ đầu câu.
- Nút nói đúng việc sẽ xảy ra: "Trò chuyện với Atlas", "Gửi lại", "Cuộc trò chuyện mới".
- Lỗi nói chuyện gì xảy ra và cách xử lý, không xin lỗi.
- Phân hệ chưa có dữ liệu thì nói rõ là chưa có. Không hiển thị dữ liệu mẫu như dữ liệu thật.

## 7. Kiểm tra trước khi hoàn thành một màn hình

- [ ] Chỉ dùng token và component dùng chung.
- [ ] Không có các mẫu bị loại ở mục 1.
- [ ] Màu của phân hệ lấy từ `catalog.tsx` và `noteColors.ts`.
- [ ] Có đủ trạng thái loading, empty, error, success, disabled khi áp dụng.
- [ ] Mọi nút chỉ có icon đều có `label`; focus luôn nhìn thấy.
- [ ] Không tràn ngang ở 390px; kiểm tra ở 390, 768, 1024 và 1440px.
- [ ] Kiểm tra cả giao diện sáng và tối bằng ảnh chụp thật.
