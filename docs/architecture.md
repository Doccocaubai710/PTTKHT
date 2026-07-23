# Kiến trúc hệ thống

## 1. Kiến trúc logic — 3 lớp (Layered Architecture)

```
┌──────────────────────────────────────────────────────────┐
│  Presentation Layer  —  src/app/pages/                     │
│  (NiceGUI pages: login/register, search, field detail,      │
│   my-bookings, owner dashboard, staff counter)               │
│  - Nhận thao tác người dùng (click, nhập liệu)                │
│  - Validate dữ liệu cơ bản (bắt buộc nhập, định dạng)          │
│  - Gọi Service tương ứng, hiển thị kết quả/lỗi                 │
│  - Kiểm tra JWT trong phiên (app/pages/guards.py) trước khi     │
│    hiển thị trang, tương đương middleware auth của REST API     │
└───────────────────────────┬────────────────────────────────┘
                            │ gọi
┌───────────────────────────▼────────────────────────────────┐
│  Business Logic Layer  —  src/app/services/                  │
│  (AuthService, FieldService, BookingService, ReviewService)    │
│  - Toàn bộ nghiệp vụ: validate ràng buộc nghiệp vụ, tính tiền   │
│    cọc, chính sách hoàn cọc, state machine của Booking,         │
│    chống trùng lịch (bắt IntegrityError), phát hành JWT         │
│  - Không phụ thuộc UI — có thể unit test độc lập                │
└───────────────────────────┬────────────────────────────────┘
                            │ gọi
┌───────────────────────────▼────────────────────────────────┐
│  Data Access Layer  —  src/app/repositories/                  │
│  (UserRepository, FieldRepository, FieldTimeSlotRepository,     │
│   BookingRepository, ReviewRepository)                         │
│  - CRUD thuần túy qua SQLAlchemy Session, không chứa business   │
│    rule                                                         │
└───────────────────────────┬────────────────────────────────┘
                            │ đọc/ghi
┌───────────────────────────▼────────────────────────────────┐
│  Database  —  SQLite (file data/sportbook.db)                 │
│  - Bảng: users, fields, field_time_slots, bookings, reviews     │
│  - Ràng buộc toàn vẹn: unique(phone), unique(email),            │
│    unique(booking_id) trên reviews, và đặc biệt: PARTIAL         │
│    UNIQUE INDEX trên bookings(field_id, booking_date,            │
│    time_slot_id) WHERE status IN (PENDING, CONFIRMED, COMPLETED) │
└──────────────────────────────────────────────────────────┘
```

`src/app/models/` (entity SQLAlchemy) và `src/app/core/` (config, kết nối DB, bảo
mật) là hai thành phần dùng chung, được cả 3 lớp trên tham chiếu tới (xem
`docs/diagram-drafts/package-diagram.md` để biết chi tiết chiều phụ thuộc).

## 2. Kiến trúc triển khai (deployment / client-server)

Vì dùng NiceGUI (server-rendered UI qua WebSocket, xây trên FastAPI + Starlette +
Uvicorn), mô hình triển khai đơn giản hơn một SPA + REST API truyền thống:

```
┌───────────────┐   HTTP (tải trang lần đầu)   ┌─────────────────────────────┐
│   Trình duyệt  │ ───────────────────────────>│  Uvicorn (ASGI server)        │
│   (Khách hàng, │                              │   └─ FastAPI/Starlette app     │
│   Chủ sân,     │ <────────────────────────────│      └─ NiceGUI runtime         │
│   Nhân viên)   │   WebSocket (mọi sự kiện UI:  │         └─ app/pages/*.py       │
│                │   click, nhập liệu, cập nhật  │            (Presentation)       │
└───────────────┘   DOM diff...)                │         └─ app/services/*.py    │
                                                  │            (Business Logic)     │
                                                  │         └─ app/repositories/    │
                                                  │            (Data Access)        │
                                                  │         └─ SQLite file           │
                                                  └─────────────────────────────┘
```

- Toàn bộ logic (kể cả xử lý sự kiện nút bấm) chạy **trên server**, trong cùng
  một tiến trình Python; trình duyệt chỉ render DOM và gửi sự kiện qua WebSocket.
  Điều này khác với kiến trúc React/Express dự kiến ban đầu (client gọi REST API
  riêng biệt), nhưng vẫn giữ nguyên sự tách bạch 3 lớp ở phía server.
- Không có tiến trình/service độc lập nào khác (không microservice, không cache
  Redis, không message queue) — phù hợp quy mô đồ án 1 tuần và dữ liệu demo.
- Một **background task** (`asyncio.create_task` trong `app/main.py`) chạy song
  song trong cùng tiến trình, định kỳ 30 giây gọi
  `BookingService.expire_overdue_bookings()` để tự động chuyển các booking
  `PENDING` quá hạn giữ chỗ sang `EXPIRED`.

## 3. Các mẫu thiết kế (design pattern) đã áp dụng

| Pattern | Áp dụng ở đâu | Lý do chọn |
|---|---|---|
| **Repository Pattern** | `src/app/repositories/*.py` | Tách biệt truy vấn dữ liệu (SQLAlchemy Session, câu lệnh `select()`) khỏi nghiệp vụ; Service không cần biết chi tiết ORM, giúp dễ thay đổi cách lưu trữ hoặc viết test với repository giả (fake) mà không đụng tới business logic. |
| **Service Layer Pattern** | `src/app/services/*.py` | Gom toàn bộ nghiệp vụ (validate, tính toán, state machine) vào một nơi duy nhất cho mỗi domain (Auth/Field/Booking/Review), tránh lặp lại logic ở nhiều trang UI khác nhau — VD `pay_deposit` được cả UC004 (khách tự thanh toán) và UC007 (nhân viên xác nhận tiền mặt) dùng chung. |
| **Anemic Domain Model có chủ đích** | `src/app/models/*.py` | Entity (`Booking`, `Field`...) chỉ chứa thuộc tính + quan hệ ORM, không chứa nghiệp vụ — nghiệp vụ đặt hết ở Service. Lựa chọn này giúp đồ án dễ giải thích ranh giới 3 lớp một cách tường minh, dù không phải là "rich domain model" thuần túy theo DDD. |
| **State Pattern (dạng khai báo, không dùng class-per-state)** | `ALLOWED_TRANSITIONS` + `validate_transition()` trong `booking_service.py` | Thay vì tạo một class riêng cho mỗi trạng thái (State Pattern cổ điển, dễ over-engineering cho 5 trạng thái đơn giản), dùng một bảng tra cứu (dict) khai báo tường minh các transition hợp lệ — vẫn đảm bảo tính đúng đắn và dễ đọc, phù hợp quy mô đồ án. |
| **Context Manager cho Unit of Work** | `get_session()` trong `core/database.py` | Đảm bảo mỗi thao tác nghiệp vụ mở đúng 1 transaction, tự `commit()` khi thành công và `rollback()` khi có lỗi (kể cả `IntegrityError` do trùng lịch), tránh rò rỉ session hoặc để transaction treo lơ lửng. |
| **Guard Clause / Route Guard** | `app/pages/guards.py` (`require_login`, `require_role`) | Kiểm tra JWT và vai trò người dùng trước khi render một trang — tương đương middleware xác thực của một REST API, nhưng triển khai dưới dạng hàm gọi ở đầu mỗi page function vì NiceGUI không có khái niệm middleware theo route như Express. |
| **DTO đơn giản qua `dataclass`** | `AuthResult`, `CancelResult`, `SlotAvailability` trong các service | Đóng gói dữ liệu trả về từ Service cho Presentation layer thành một cấu trúc rõ ràng, tránh trả về tuple không tên hoặc dict thiếu kiểu, dù không cần tới một lớp DTO đầy đủ như khi có REST API JSON serialize riêng. |

## 4. Vì sao chọn NiceGUI thay vì Node.js/Express/React (ghi chú cho báo cáo)

Đề bài ban đầu dự kiến Node.js + Express + Prisma + React. Trong quá trình triển
khai, môi trường phát triển thực tế **không có sẵn Node.js/npm**, trong khi đã có
sẵn Python + conda. Theo yêu cầu của người thực hiện đồ án, toàn bộ hệ thống được
chuyển sang 100% Python bằng NiceGUI — framework cho phép viết cả UI và xử lý sự
kiện bằng Python thuần (nút bấm gọi thẳng hàm Python), giúp:

- Cài đặt & chạy được trong 1 lệnh `pip install -r requirements.txt`, không cần
  cài thêm runtime nào khác ngoài Python.
- Vẫn giữ được đầy đủ 3 lớp kiến trúc và toàn bộ yêu cầu kỹ thuật trọng tâm (chống
  trùng lịch bằng unique constraint + transaction, state machine, JWT, validate
  client/server) — không đánh đổi độ sâu kỹ thuật của đồ án.
- Đánh đổi: không minh họa được kiến trúc "SPA gọi REST API" kinh điển (client-
  server tách rời hoàn toàn qua HTTP JSON) như đề bài gốc dự kiến với React; thay
  vào đó minh họa mô hình server-rendered qua WebSocket. Phần "REST API" trong yêu
  cầu ban đầu được thay thế bằng lời gọi hàm Python trực tiếp giữa Presentation và
  Business Logic layer (cùng tiến trình), nhưng ranh giới trách nhiệm giữa các lớp
  vẫn được giữ nguyên vẹn để phục vụ mục tiêu học thuật của đồ án.
