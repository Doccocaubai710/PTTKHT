# Draft — State Machine Diagram cho Booking

> Nguồn implement: `src/app/services/booking_service.py` (`ALLOWED_TRANSITIONS`,
> `validate_transition`) và `src/app/models/booking.py`.

## Danh sách trạng thái (state)

| State | Ý nghĩa |
|---|---|
| `PENDING` | Vừa tạo booking, đang giữ chỗ tạm thời, chờ khách thanh toán cọc |
| `CONFIRMED` | Đã xác nhận, đã thanh toán cọc (mock hoặc tiền mặt) |
| `COMPLETED` | Khách đã sử dụng sân xong, đã được Nhân viên check-in |
| `CANCELLED` | Khách hủy đặt sân (từ PENDING hoặc CONFIRMED) |
| `EXPIRED` | Quá thời gian giữ chỗ (10 phút) mà khách chưa thanh toán |

`PENDING`, `CONFIRMED`, `COMPLETED` là các state **"đang chiếm chỗ"** (active) —
được dùng làm điều kiện lọc trong partial unique index chống trùng lịch.
`CANCELLED`, `EXPIRED` là **state kết thúc (final state)**, không có transition đi
ra khỏi 2 trạng thái này.

## Bảng transition đầy đủ

| Từ state | Đến state | Sự kiện kích hoạt (event) | Điều kiện (guard) | Nơi xử lý |
|---|---|---|---|---|
| *(khởi tạo)* | `PENDING` | Khách hàng đặt sân (UC003) hoặc Nhân viên đặt hộ (UC007) | Khung giờ chưa bị chiếm bởi booking active nào khác (đảm bảo bởi partial unique index) | `BookingService.create_booking` |
| `PENDING` | `CONFIRMED` | Khách hàng thanh toán cọc (UC004) hoặc Nhân viên xác nhận tiền mặt (UC007) | `now <= hold_expires_at` (chưa quá 10 phút giữ chỗ) | `BookingService.pay_deposit` |
| `PENDING` | `CANCELLED` | Khách hàng hủy khi chưa thanh toán (UC005) | Không có (luôn được phép khi đang PENDING) | `BookingService.cancel_booking` |
| `PENDING` | `EXPIRED` | Job nền định kỳ (mỗi 30s) phát hiện quá hạn giữ chỗ, hoặc phát hiện ngay khi khách cố thanh toán trễ | `now > hold_expires_at` | `BookingService.expire_overdue_bookings` / `_expire` (gọi từ `pay_deposit`) |
| `CONFIRMED` | `COMPLETED` | Nhân viên check-in sau khi khách sử dụng sân xong (UC007) | Không kiểm tra thêm điều kiện thời gian trong bản baseline (đơn giản hóa cho demo) | `BookingService.check_in_and_complete` |
| `CONFIRMED` | `CANCELLED` | Khách hàng hủy sau khi đã đặt cọc (UC005) | Áp dụng chính sách hoàn cọc theo số giờ còn lại đến giờ chơi: `>=24h` hoàn 100%, `6–24h` hoàn 50%, `<6h` hoàn 0% | `BookingService.cancel_booking` |
| `COMPLETED` | *(không có)* | — | — | State kết thúc, không transition nào được phép đi ra |
| `CANCELLED` | *(không có)* | — | — | State kết thúc |
| `EXPIRED` | *(không có)* | — | — | State kết thúc |

## Các transition KHÔNG hợp lệ (bị từ chối tường minh)

Mọi cặp (từ, đến) không nằm trong bảng trên đều bị `validate_transition()` từ chối,
ném `BookingError`. Một số ví dụ hay gặp cần lưu ý khi kiểm thử/báo cáo:

- `COMPLETED → PENDING` (không thể "quay lại" sau khi đã hoàn tất)
- `CANCELLED → CONFIRMED` (không thể khôi phục một booking đã hủy)
- `EXPIRED → CONFIRMED` (không thể thanh toán cho một booking đã hết hạn — khách
  phải tạo booking mới)
- `PENDING → COMPLETED` (không thể bỏ qua bước CONFIRMED)

## Vẽ tay gợi ý (dạng text mô tả sơ đồ)

```
        [*] 
         |  create_booking (UC003/UC007)
         v
     ┌─────────┐   pay_deposit trong hạn (UC004/UC007)   ┌───────────┐
     │ PENDING │ ───────────────────────────────────────>│ CONFIRMED │
     └─────────┘                                          └───────────┘
       |     |                                               |     |
       |     | quá hạn giữ chỗ (job nền / _expire)           |     | check_in (UC007)
       |     v                                               |     v
       |  ┌─────────┐                                        |  ┌───────────┐
       |  │ EXPIRED │ [*]                                    |  │ COMPLETED │ [*]
       |  └─────────┘                                        |  └───────────┘
       | hủy khi chưa cọc (UC005)                             | hủy sau khi đã cọc,
       v                                                       | áp dụng chính sách hoàn cọc (UC005)
   ┌───────────┐                                               v
   │ CANCELLED │ [*] <───────────────────────────────────────────┘
   └───────────┘
```
