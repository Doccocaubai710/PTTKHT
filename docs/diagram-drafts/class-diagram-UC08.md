# Draft — Class Diagram cho UC08 (Đặt sân)

## Danh sách lớp tham gia

### 1. `FieldDetailPage` (presentation — `app/pages/customer_pages.py::field_detail_page`)
- Không phải class thật sự trong code (là hàm), nhưng khi vẽ UML có thể biểu diễn
  như một "Boundary class" theo mẫu Robustness Diagram nếu môn học yêu cầu.
- Phương thức chính: `book_slot(slot_id)`, `refresh_slots()`

### 2. `BookingService` (business logic — `app/services/booking_service.py`)
- Thuộc tính: `booking_repo: BookingRepository`, `slot_repo: FieldTimeSlotRepository`
- Phương thức chính:
  - `create_booking(field_id, time_slot_id, booking_date, customer_id, created_by_id) -> Booking`
  - `validate_transition(current, target) -> None` (module-level function, có thể vẽ như static method)

### 3. `BookingRepository` (data access — `app/repositories/booking_repository.py`)
- Phương thức chính: `add(session, booking)`, `list_booked_slot_ids(session, field_id, date)`

### 4. `FieldTimeSlotRepository` (data access — `app/repositories/field_repository.py`)
- Phương thức chính: `get_by_id(session, slot_id)`

### 5. `Booking` (entity — `app/models/booking.py`)
- Thuộc tính: `id: int`, `field_id: int`, `time_slot_id: int`, `booking_date: date`,
  `customer_id: int`, `created_by_id: int`, `status: BookingStatus`,
  `total_price: float`, `deposit_amount: float`, `is_deposit_paid: bool`,
  `hold_expires_at: datetime`, `reschedule_count: int`
- Phương thức: không có nghiệp vụ trong entity (anemic domain model theo chủ đích —
  nghiệp vụ đặt ở `BookingService` để dễ test độc lập với ORM)

### 6. `FieldTimeSlot` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `field_id: int`, `start_time: time`, `end_time: time`,
  `price: float`, `is_active: bool`

### 7. `Field` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `facility_id: int`, `name: str`, `sport_type: SportType`,
  `description: str | None`
- **Khác biệt so với bản trước:** `owner_id`/`area`/`address` không còn nằm trực
  tiếp trên `Field` — đã tách sang `Facility` (xem
  `docs/diagram-drafts/class-diagram-UC13-UC24.md`). `Field.facility_id` là khóa
  ngoại tới `Facility`.

### 8. `BookingStatus` (enum — `app/models/enums.py`)
- Giá trị: `PENDING, AWAITING_CONFIRMATION, CONFIRMED, COMPLETED, CANCELLED, EXPIRED`

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `FieldDetailPage` | `BookingService` | Dependency (gọi phương thức, không giữ tham chiếu lâu dài) | 1..1 |
| `BookingService` | `BookingRepository` | Association (composition theo vòng đời — được khởi tạo cùng service) | 1..1 |
| `BookingService` | `FieldTimeSlotRepository` | Association | 1..1 |
| `BookingRepository` | `Booking` | Dependency (tạo/truy vấn, không sở hữu vòng đời) | 1..n |
| `Field` | `FieldTimeSlot` | Composition (khung giờ không có ý nghĩa tồn tại độc lập ngoài 1 sân; xoá sân thì xoá luôn khung giờ — `cascade="all, delete-orphan"`) | 1 — n |
| `Field` | `Booking` | Association | 1 — n |
| `FieldTimeSlot` | `Booking` | Association | 1 — n |
| `Booking` | `BookingStatus` | Association (thuộc tính kiểu enum) | 1 — 1 |

## Ghi chú thiết kế đáng chú ý khi vẽ

- `Booking` có ràng buộc **unique index** trên tổ hợp `(field_id, booking_date,
  time_slot_id)` (chỉ tính khi `status` thuộc {PENDING, AWAITING_CONFIRMATION,
  CONFIRMED, COMPLETED}) — nên ghi chú (constraint note) đính kèm lớp `Booking`
  trên class diagram, vì đây là ràng buộc dữ liệu quan trọng nhất của UC08, không
  thể hiện được qua bội số association thông thường.
- `BookingRepository`/`FieldTimeSlotRepository` không giữ session — session được
  truyền vào theo tham số (`get_session()` ở tầng service quản lý vòng đời), nên
  không vẽ association giữa repository và session.
