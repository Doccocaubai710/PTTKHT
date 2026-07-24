# Draft — Class Diagram cho UC13 + UC24 (Đăng ký cơ sở sân & Duyệt cơ sở sân mới)

> Vẽ chung một file vì đây là chuỗi 2 use case của 2 actor khác nhau xoay quanh
> đúng một entity mới, quan trọng nhất trong lần cập nhật này: `Facility`
> (Cơ sở sân) — thực thể **không tồn tại** trong bản baseline ban đầu (nơi `Field`
> gắn `owner_id`/`area`/`address` trực tiếp, không có khái niệm "cơ sở" và không có
> quy trình duyệt).

## Danh sách lớp tham gia

### 1. `OwnerDashboardPage` (presentation — `app/pages/owner_pages.py`)
- Phương thức chính: `new_facility_dialog(on_created)`, `edit_facility_dialog(facility, on_updated)` (UC13)

### 2. `AdminFacilitiesPage` (presentation — `app/pages/admin_pages.py::admin_facilities_page`)
- Phương thức chính: `approve(facility_id)`, `reject_dialog(facility_id)` (UC24)

### 3. `FacilityService` (business logic — `app/services/facility_service.py`)
- Thuộc tính: `facility_repo: FacilityRepository`
- Phương thức chính:
  - `register_facility(owner_id, name, area, address, description, cancellation_policy) -> Facility` (UC13)
  - `update_facility(facility_id, owner_id, ...) -> Facility` (UC13, chỉnh sửa & gửi lại)
  - `list_pending_facilities() -> list[Facility]` (UC24)
  - `approve_facility(facility_id, admin_id) -> Facility` (UC24)
  - `reject_facility(facility_id, admin_id, reason) -> Facility` (UC24)

### 4. `FacilityRepository` (data access — `app/repositories/facility_repository.py`)
- Phương thức chính: `add(session, facility)`, `get_by_id(session, facility_id)`,
  `list_by_owner(session, owner_id)`, `list_by_status(session, status)`,
  `list_approved(session, area)`

### 5. `Facility` (entity — `app/models/facility.py`)
- Thuộc tính: `id: int`, `owner_id: int`, `name: str`, `area: str`, `address: str`,
  `description: str | None`, `cancellation_policy: str | None`,
  `status: FacilityStatus`, `reject_reason: str | None`,
  `reviewed_by_id: int | None`, `reviewed_at: datetime | None`

### 6. `FacilityStatus` (enum — `app/models/enums.py`)
- Giá trị: `PENDING, APPROVED, REJECTED`

### 7. `Field` (entity — `app/models/field.py`)
- Thuộc tính liên quan: `facility_id: int` (khóa ngoại tới `Facility`)

### 8. `User` (entity — `app/models/user.py`)
- Vai trò `FIELD_OWNER` (chủ sở hữu, `Facility.owner_id`) và `ADMIN` (người duyệt,
  `Facility.reviewed_by_id`)

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `OwnerDashboardPage` | `FacilityService` | Dependency | 1..1 |
| `AdminFacilitiesPage` | `FacilityService` | Dependency | 1..1 |
| `FacilityService` | `FacilityRepository` | Association | 1..1 |
| `FacilityRepository` | `Facility` | Dependency | 1..n |
| `User` (Chủ sân) | `Facility` | Association ("sở hữu", qua `owner_id`) | 1 — n |
| `User` (Quản trị viên) | `Facility` | Association ("duyệt", qua `reviewed_by_id`) | 0..1 — n |
| `Facility` | `FacilityStatus` | Association (thuộc tính kiểu enum) | 1 — 1 |
| `Facility` | `Field` | Composition (một Sân luôn thuộc đúng 1 Cơ sở sân) | 1 — n |

## Ghi chú thiết kế đáng chú ý khi vẽ

- `Facility` là entity **mới hoàn toàn**, tách từ những gì trước đây nằm trên
  `Field` (`owner_id`, `area`, `address`, `description`) — đây là điểm cần nhấn
  mạnh nhất khi báo cáo về sự khác biệt cấu trúc so với thiết kế trước.
- `Facility.status` mặc định `PENDING` khi tạo mới (UC13) — **không** có đường
  transition trực tiếp nào cho phép một Chủ sân tự chuyển `status` sang `APPROVED`;
  chỉ `FacilityService.approve_facility` (gọi từ trang của Quản trị viên, UC24) mới
  được phép làm điều này. Đây là một ràng buộc nghiệp vụ quan trọng nên vẽ ghi chú
  (note) đính kèm lớp `Facility` hoặc thể hiện qua một state diagram riêng
  (`PENDING → APPROVED` / `PENDING → REJECTED`, không có transition ngược từ
  `APPROVED`).
- Các Sân (`Field`) và khung giờ (`FieldTimeSlot`) bên trong một `Facility` đang
  `PENDING`/`REJECTED` **vẫn tồn tại bình thường trong CSDL** (Chủ sân vẫn thao tác
  được ở UC14/UC15) nhưng bị lọc khỏi kết quả tìm kiếm công khai ở UC05
  (`FieldRepository.search(..., approved_only=True)`) — đây là một ràng buộc ở tầng
  **truy vấn** (query-level), không phải ràng buộc CSDL (không có cột nào trên
  `Field` bị khóa write), nên khi vẽ activity/sequence diagram cho UC05 cần thể
  hiện rõ điều kiện lọc này.
