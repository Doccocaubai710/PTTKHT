# Draft — Class Diagram cho UC004 (Thanh toán đặt cọc - mock)

## Danh sách lớp tham gia

### 1. `MyBookingsPage` (presentation — `app/pages/customer_pages.py::my_bookings_page`)
- Phương thức chính: `pay(booking_id)`, `refresh()`

### 2. `BookingService` (business logic — `app/services/booking_service.py`)
- Phương thức chính:
  - `pay_deposit(booking_id, payment_method="MOCK_ONLINE") -> Booking`
  - `confirm_cash_payment(booking_id) -> Booking` (gọi lại `pay_deposit` với `payment_method="CASH"`, dùng ở UC007)
  - `_expire(booking)` (helper nội bộ, chuyển PENDING quá hạn sang EXPIRED)

### 3. `BookingRepository` (data access — `app/repositories/booking_repository.py`)
- Phương thức chính: `get_by_id(session, booking_id)`

### 4. `Booking` (entity — `app/models/booking.py`)
- Thuộc tính liên quan: `status`, `is_deposit_paid`, `payment_method`, `hold_expires_at`, `deposit_amount`

### 5. `BookingStatus` (enum — `app/models/enums.py`)

### 6. (Ghi chú) `MockPaymentGateway` — **thành phần giả lập, không có class thật trong code**
- Vì đồ án yêu cầu KHÔNG tích hợp cổng thanh toán thật, "cổng thanh toán" chỉ tồn
  tại dưới dạng một đoạn xử lý luôn trả về thành công bên trong
  `BookingService.pay_deposit` (không tách class riêng để tránh over-engineering
  cho một thành phần luôn trả kết quả cố định). Khi vẽ tay, có thể vẽ một class
  `MockPaymentGateway` với method `charge(amount) -> True` và ghi chú
  "«mock», luôn trả về thành công" để minh họa rõ ranh giới tích hợp trong tương
  lai, dù hiện tại logic này nằm inline trong service.

## Quan hệ giữa các lớp

| Từ lớp | Đến lớp | Loại quan hệ | Bội số |
|---|---|---|---|
| `MyBookingsPage` | `BookingService` | Dependency | 1..1 |
| `BookingService` | `BookingRepository` | Association | 1..1 |
| `BookingService` | `MockPaymentGateway` (ghi chú) | Dependency («mock») | 1..1 |
| `BookingRepository` | `Booking` | Dependency | 1..n |
| `Booking` | `BookingStatus` | Association | 1—1 |

## Ghi chú thiết kế

- State machine (`ALLOWED_TRANSITIONS`) được kiểm tra tại `pay_deposit` trước khi
  đổi `status`, đảm bảo không thể "thanh toán cọc" cho một booking đã
  `CANCELLED`/`EXPIRED`/`COMPLETED`.
- `payment_method` là `str` tự do (`"MOCK_ONLINE"` hoặc `"CASH"`) thay vì enum
  riêng, vì đồ án chỉ cần phân biệt 2 kênh mô phỏng, không cần mở rộng thêm.
