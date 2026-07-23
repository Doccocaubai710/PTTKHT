# Draft — Class Diagram cho UC006 (Quản lý khung giờ & giá sân)

## Danh sách lớp tham gia

### 1. `OwnerDashboardPage` (presentation — `app/pages/owner_pages.py::owner_dashboard_page`)
- Phương thức chính: `refresh()`, `new_field_dialog(on_created)`, hàm lồng
  `save_price(slot_id, price)`, `toggle_active(slot_id, is_active)`, `add_slot(...)`

### 2. `FieldService` (business logic — `app/services/field_service.py`)
- Thuộc tính: `field_repo: FieldRepository`, `slot_repo: FieldTimeSlotRepository`
- Phương thức chính:
  - `create_field(owner_id, name, sport_type, area, address, description) -> Field`
  - `list_owner_fields(owner_id) -> list[Field]`
  - `add_time_slot(field_id, start_time, end_time, price) -> FieldTimeSlot`
  - `update_time_slot_price(slot_id, price) -> None`
  - `set_time_slot_active(slot_id, is_active) -> None`
  - `list_time_slots(field_id) -> list[FieldTimeSlot]`

### 3. `FieldRepository` (data access — `app/repositories/field_repository.py`)
- Phương thức chính: `add(session, field)`, `list_by_owner(session, owner_id)`

### 4. `FieldTimeSlotRepository` (data access — `app/repositories/field_repository.py`)
- Phương thức chính: `add(session, slot)`, `get_by_id(session, slot_id)`,
  `list_by_field(session, field_id, active_only)`

### 5. `Field` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `owner_id: int`, `name: str`, `sport_type: SportType`,
  `area: str`, `address: str`, `description: str | None`

### 6. `FieldTimeSlot` (entity — `app/models/field.py`)
- Thuộc tính: `id: int`, `field_id: int`, `start_time: time`, `end_time: time`,
  `price: float`, `is_active: bool`

### 7. `User` (entity — `app/models/user.py`, vai trò FIELD_OWNER)
- Thuộc tính liên quan: `id: int`, `role: UserRole`

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `OwnerDashboardPage` | `FieldService` | Dependency | 1..1 |
| `FieldService` | `FieldRepository` | Association | 1..1 |
| `FieldService` | `FieldTimeSlotRepository` | Association | 1..1 |
| `User` (Chủ sân) | `Field` | Association ("sở hữu") | 1 — n |
| `Field` | `FieldTimeSlot` | **Composition** (khung giờ không tồn tại độc lập ngoài 1 sân cụ thể; xóa Field sẽ xóa theo toàn bộ FieldTimeSlot — `cascade="all, delete-orphan"` trong SQLAlchemy) | 1 — n |
| `FieldRepository` | `Field` | Dependency | 1..n |
| `FieldTimeSlotRepository` | `FieldTimeSlot` | Dependency | 1..n |

## Ghi chú thiết kế

- `owner_id` trên `Field` chính là khóa ngoại tới `User.id` — khi vẽ, biểu diễn
  quan hệ Association 1-n từ `User` đến `Field` với vai trò (role name) "owner".
- Composition giữa `Field` và `FieldTimeSlot` là điểm quan trọng cần thể hiện đúng
  ký hiệu UML (hình thoi đặc ở đầu `Field`) vì nó phản ánh đúng ràng buộc
  `cascade="all, delete-orphan"` trong code — nhấn mạnh khung giờ phụ thuộc hoàn
  toàn vào vòng đời của sân.
