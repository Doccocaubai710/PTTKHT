# Draft — Class Diagram cho UC14 (Quản lý sân và khung giờ)

## Danh sách lớp tham gia

### 1. `OwnerDashboardPage` (presentation — `app/pages/owner_pages.py::owner_dashboard_page`)
- Phương thức chính: `refresh()`, `new_field_dialog(facility_id, on_created)`, hàm
  lồng `save_price(slot_id, price)`, `toggle_active(slot_id, is_active)`,
  `add_slot(...)`

### 2. `FieldService` (business logic — `app/services/field_service.py`)
- Thuộc tính: `field_repo: FieldRepository`, `slot_repo: FieldTimeSlotRepository`,
  `facility_repo: FacilityRepository`
- Phương thức chính:
  - `create_field(owner_id, facility_id, name, sport_type, description) -> Field`
  - `list_owner_fields(owner_id) -> list[Field]`, `list_facility_fields(facility_id) -> list[Field]`
  - `add_time_slot(field_id, start_time, end_time, price) -> FieldTimeSlot`
  - `update_time_slot_price(slot_id, price) -> None` (UC15)
  - `set_time_slot_active(slot_id, is_active) -> None` (UC15)
  - `list_time_slots(field_id) -> list[FieldTimeSlot]`

### 3. `FieldRepository` (data access — `app/repositories/field_repository.py`)
- Phương thức chính: `add(session, field)`, `list_by_facility(session, facility_id)`,
  `list_by_owner(session, owner_id)` (JOIN qua `Facility`)

### 4. `FieldTimeSlotRepository` (data access — `app/repositories/field_repository.py`)
- Phương thức chính: `add(session, slot)`, `get_by_id(session, slot_id)`,
  `list_by_field(session, field_id, active_only)`

### 5. `Field` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `facility_id: int`, `name: str`, `sport_type: SportType`,
  `description: str | None`

### 6. `FieldTimeSlot` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `field_id: int`, `start_time: time`, `end_time: time`,
  `price: float`, `is_active: bool`

### 7. `Facility` (entity — `app/models/facility.py`)
- Thuộc tính liên quan: `id: int`, `owner_id: int`, `status: FacilityStatus`
- Xem chi tiết đầy đủ tại `docs/diagram-drafts/class-diagram-UC13-UC24.md`

### 8. `User` (entity — `app/models/user.py`, vai trò FIELD_OWNER)
- Thuộc tính liên quan: `id: int`, `role: UserRole`

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `OwnerDashboardPage` | `FieldService` | Dependency | 1..1 |
| `FieldService` | `FieldRepository` | Association | 1..1 |
| `FieldService` | `FieldTimeSlotRepository` | Association | 1..1 |
| `FieldService` | `FacilityRepository` | Association (kiểm tra `facility.owner_id == owner_id` trước khi tạo Field) | 1..1 |
| `User` (Chủ sân) | `Facility` | Association ("sở hữu") | 1 — n |
| `Facility` | `Field` | **Composition** (một Sân luôn thuộc về đúng 1 Cơ sở sân; xóa Facility sẽ xóa theo toàn bộ Field — `cascade="all, delete-orphan"`) | 1 — n |
| `Field` | `FieldTimeSlot` | **Composition** (khung giờ không tồn tại độc lập ngoài 1 sân cụ thể; xóa Field sẽ xóa theo toàn bộ FieldTimeSlot — `cascade="all, delete-orphan"`) | 1 — n |
| `FieldRepository` | `Field` | Dependency | 1..n |
| `FieldTimeSlotRepository` | `FieldTimeSlot` | Dependency | 1..n |

## Ghi chú thiết kế

- **Thay đổi cấu trúc quan trọng nhất so với bản trước:** `owner_id` không còn nằm
  trực tiếp trên `Field` — quan hệ sở hữu là `User (Chủ sân) → Facility → Field`
  (2 cấp), không phải `User → Field` (1 cấp) như bản baseline ban đầu. Điều này
  cho phép một Chủ sân có nhiều Cơ sở sân, mỗi cơ sở có nhiều Sân với các loại thể
  thao khác nhau, và tách đúng điểm cần duyệt (UC24) ra khỏi từng Sân riêng lẻ.
- `FieldService.create_field` phải xác minh `facility_id` thuộc `owner_id` đang
  gọi trước khi cho tạo Sân — đây là điểm kiểm soát quyền quan trọng cần thể hiện
  trên sequence diagram (guard condition), không chỉ là một phép gán khóa ngoại.
- Composition giữa `Field` và `FieldTimeSlot` (và giữa `Facility` và `Field`) là
  điểm quan trọng cần thể hiện đúng ký hiệu UML (hình thoi đặc ở đầu lớp "cha").
