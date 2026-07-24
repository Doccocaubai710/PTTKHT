# Draft — Class Diagram cho UC09 + UC18 (Thanh toán đặt cọc & Xác nhận thanh toán)

> Hai use case này được vẽ chung một file vì chia sẻ đúng một nhóm entity/service
> và thể hiện rõ nhất luồng "2 actor, 2 bước" mà đề bài yêu cầu (mục 2.2.2): Người
> chơi nộp minh chứng (UC09) → Nhân viên đối chiếu & xác nhận (UC18).

## Danh sách lớp tham gia

### 1. `MyBookingsPage` (presentation — `app/pages/customer_pages.py::my_bookings_page`)
- Phương thức chính: `submit_proof_dialog(booking_id)` (UC09)

### 2. `StaffTodayPage` (presentation — `app/pages/staff_pages.py::staff_today_page`)
- Phương thức chính: `confirm_online(booking_id)`, `reject_dialog(booking_id)`,
  `confirm_cash(booking_id)` (UC18)

### 3. `BookingService` (business logic — `app/services/booking_service.py`)
- Phương thức chính liên quan:
  - `submit_payment_proof(booking_id, customer_id, proof_ref) -> Booking` (UC09)
  - `confirm_payment(booking_id, staff_id) -> Booking` (UC18, nhánh khớp)
  - `reject_payment(booking_id, staff_id, reason) -> Booking` (UC18, nhánh từ chối)
  - `confirm_cash_payment(booking_id, staff_id) -> Booking` (UC18, nhánh tiền mặt)

### 4. `BookingRepository` (data access — `app/repositories/booking_repository.py`)
- Phương thức chính: `get_by_id(session, booking_id)`

### 5. `Booking` (entity — `app/models/booking.py`)
- Thuộc tính liên quan: `status`, `is_deposit_paid`, `payment_method`,
  `payment_proof_ref`, `payment_rejected_reason`, `confirmed_by_id`,
  `hold_expires_at`, `deposit_amount`

### 6. `BookingStatus` (enum — `app/models/enums.py`)
- Giá trị liên quan tới 2 UC này: `PENDING`, `AWAITING_CONFIRMATION`, `CONFIRMED`

### 7. `User` (entity — `app/models/user.py`)
- Vai trò `CUSTOMER` (người nộp minh chứng) và `STAFF` (người xác nhận,
  `Booking.confirmed_by_id` trỏ tới `User.id` của Nhân viên này)

### 8. (Ghi chú) `PaymentGateway`/`BankStatement` — **không có class thật trong code**
- Vì đồ án không tích hợp cổng thanh toán/ngân hàng thật, việc "đối chiếu" ở UC18
  là một hành động **thủ công của con người** (Nhân viên tự mở app ngân hàng, so
  sánh bằng mắt) — không có class nào gọi API ngân hàng. Khi vẽ tay, có thể thêm
  một actor phụ/note "«manual», đối chiếu ngoài hệ thống" cạnh bước xác nhận, để
  làm rõ ranh giới tích hợp cho báo cáo.

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `MyBookingsPage` | `BookingService` | Dependency | 1..1 |
| `StaffTodayPage` | `BookingService` | Dependency | 1..1 |
| `BookingService` | `BookingRepository` | Association | 1..1 |
| `BookingRepository` | `Booking` | Dependency | 1..n |
| `Booking` | `BookingStatus` | Association | 1—1 |
| `Booking` | `User` (qua `confirmed_by_id`) | Association ("người xác nhận") | 0..1 — 1 |

## Ghi chú thiết kế

- State machine (`ALLOWED_TRANSITIONS`) được kiểm tra tại cả 4 phương thức trước
  khi đổi `status`, đảm bảo không thể xác nhận/từ chối một booking đã
  `CANCELLED`/`EXPIRED`/`COMPLETED`.
- `payment_method` là `str` tự do (`"ONLINE_QR"` hoặc `"CASH"`) thay vì enum riêng,
  vì đồ án chỉ cần phân biệt 2 kênh mô phỏng, không cần mở rộng thêm.
- **Khác biệt lớn nhất so với bản trước:** bản baseline cũ có một hàm `pay_deposit`
  duy nhất, tự động chuyển `PENDING → CONFIRMED` ngay khi khách bấm "thanh toán"
  (không có bước con người xác nhận). Bản hiện tại tách rõ UC09 (khách nộp minh
  chứng, việc của khách) và UC18 (nhân viên đối chiếu & xác nhận/từ chối, việc của
  nhân viên) thành 2 use case với 2 actor khác nhau, đúng theo quy trình nghiệp vụ
  mô tả ở đề bài (mục 2.2.2, bước 8–11) và tránh tình trạng đặt sân "ảo" mà không
  ai xác nhận thật.
