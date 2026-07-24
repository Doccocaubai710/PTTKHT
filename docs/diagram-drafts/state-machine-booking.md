# Draft — State Machine Diagram cho Booking

> Nguồn implement: `src/app/services/booking_service.py` (`ALLOWED_TRANSITIONS`,
> `validate_transition`) và `src/app/models/booking.py`.

## Danh sách trạng thái (state)

| State | Ý nghĩa |
|---|---|
| `PENDING` | Vừa tạo booking (UC08) hoặc bị Nhân viên từ chối minh chứng (UC18), đang giữ chỗ tạm thời, chờ khách nộp minh chứng thanh toán |
| `AWAITING_CONFIRMATION` | Khách đã nộp minh chứng chuyển khoản (UC09), chờ Nhân viên đối chiếu (UC18) |
| `CONFIRMED` | Đã xác nhận thanh toán (chuyển khoản khớp, hoặc tiền mặt tại quầy) |
| `COMPLETED` | Khách đã sử dụng sân xong, đã được Nhân viên check-in (UC19) |
| `CANCELLED` | Bị hủy (Người chơi tự hủy UC10, hoặc Nhân viên hủy tại chỗ UC21) |
| `EXPIRED` | Quá thời gian giữ chỗ (10 phút) mà khách chưa nộp/chưa được xác nhận minh chứng |

`PENDING`, `AWAITING_CONFIRMATION`, `CONFIRMED`, `COMPLETED` là các state
**"đang chiếm chỗ"** (active) — dùng làm điều kiện lọc trong partial unique index
chống trùng lịch. `CANCELLED`, `EXPIRED` là **state kết thúc (final state)**,
không có transition đi ra khỏi 2 trạng thái này.

Ngoài các transition đổi `status`, `Booking` còn có transition **nội tại** (không
đổi `status`) do **UC11/UC21 (đổi lịch)** gây ra: `field_id`/`time_slot_id`/
`booking_date` được cập nhật tại chỗ và `reschedule_count` tăng 1, giữ nguyên
`status` hiện tại (`PENDING`, `AWAITING_CONFIRMATION`, hoặc `CONFIRMED`) — xem ghi
chú riêng ở cuối file, không vẽ như một state mới.

## Bảng transition đầy đủ

| Từ state | Đến state | Sự kiện kích hoạt (event) | Điều kiện (guard) | Nơi xử lý |
|---|---|---|---|---|
| *(khởi tạo)* | `PENDING` | Người chơi đặt sân (UC08) hoặc Nhân viên đặt hộ (UC20) | Khung giờ chưa bị chiếm bởi booking active nào khác (đảm bảo bởi partial unique index) | `BookingService.create_booking` |
| `PENDING` | `AWAITING_CONFIRMATION` | Khách nộp minh chứng chuyển khoản (UC09) | `now <= hold_expires_at`; đã nhập `payment_proof_ref` | `BookingService.submit_payment_proof` |
| `PENDING` | `CONFIRMED` | Nhân viên xác nhận thu tiền mặt tại quầy (UC18/UC20) | Không yêu cầu minh chứng — Nhân viên trực tiếp nhận tiền | `BookingService.confirm_cash_payment` |
| `PENDING` | `CANCELLED` | Người chơi/Nhân viên hủy khi chưa nộp minh chứng (UC10/UC21) | Không có (luôn được phép) | `BookingService.cancel_booking` |
| `PENDING` | `EXPIRED` | Job nền định kỳ (mỗi 30s) phát hiện quá hạn giữ chỗ | `now > hold_expires_at` | `BookingService.expire_overdue_bookings` |
| `AWAITING_CONFIRMATION` | `CONFIRMED` | Nhân viên đối chiếu khớp minh chứng (UC18) | Không có điều kiện thời gian thêm | `BookingService.confirm_payment` |
| `AWAITING_CONFIRMATION` | `PENDING` | Nhân viên từ chối minh chứng, yêu cầu bổ sung (UC18/A1) | Không có | `BookingService.reject_payment` (gia hạn `hold_expires_at` thêm 10 phút) |
| `AWAITING_CONFIRMATION` | `CANCELLED` | Người chơi/Nhân viên hủy khi đang chờ xác nhận (UC10/UC21) | Không có | `BookingService.cancel_booking` (chưa `CONFIRMED` nên không hoàn cọc) |
| `AWAITING_CONFIRMATION` | `EXPIRED` | Job nền phát hiện quá hạn trong khi vẫn chưa được xác nhận | `now > hold_expires_at` | `BookingService.expire_overdue_bookings` |
| `CONFIRMED` | `COMPLETED` | Nhân viên check-in sau khi khách sử dụng sân xong (UC19) | Không kiểm tra thêm điều kiện thời gian (đơn giản hóa cho demo) | `BookingService.check_in_and_complete` |
| `CONFIRMED` | `CANCELLED` | Người chơi hủy (UC10) hoặc Nhân viên hủy tại chỗ (UC21) sau khi đã đặt cọc | Áp dụng chính sách hoàn cọc theo số giờ còn lại đến giờ chơi: `>=24h` hoàn 100%, `6–24h` hoàn 50%, `<6h` hoàn 0% | `BookingService.cancel_booking` |
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
- `PENDING → COMPLETED` (không thể bỏ qua bước `AWAITING_CONFIRMATION`/`CONFIRMED`)
- `AWAITING_CONFIRMATION → COMPLETED` (không thể check-in trước khi được xác nhận
  thanh toán)

## Vẽ tay gợi ý (dạng text mô tả sơ đồ)

```
        [*]
         |  create_booking (UC08/UC20)
         v
     ┌─────────┐  submit_payment_proof (UC09)   ┌────────────────────────┐
     │ PENDING │ ───────────────────────────────>│ AWAITING_CONFIRMATION  │
     └─────────┘ <─────────────────────────────── └────────────────────────┘
       |  |  |     reject_payment (UC18, A1)         |         |        |
       |  |  |                                        |         |        |
       |  |  | confirm_cash_payment (UC18/UC20)        |confirm_ |expire  |cancel
       |  |  |                                          |payment |(job)   |(UC10/21)
       |  |  +------------------------------------------+        v        v
       |  | quá hạn (job nền)                                ┌───────────┐ ┌───────────┐
       |  v                                                   │ CONFIRMED │ │ CANCELLED │[*]
       |┌─────────┐                                           └───────────┘ └───────────┘
       ||EXPIRED  │[*]                                          |     |
       |└─────────┘                                    check_in |     | cancel_booking
       | hủy khi chưa cọc                             (UC19)    |     | (UC10/21, hoàn cọc
       v (UC10/21)                                              v     |  theo giờ còn lại)
   ┌───────────┐                                          ┌───────────┐
   │ CANCELLED │[*] <──────────────────────────────────────│ COMPLETED │[*]
   └───────────┘                                            └───────────┘
```

## Ghi chú — Đổi lịch (UC11/UC21) không phải một state

`reschedule_booking` **không** đổi `status` — nó chỉ ghi đè `field_id`/
`time_slot_id`/`booking_date`/`total_price`/`deposit_amount` trên đúng bản ghi
`Booking` hiện tại và tăng `reschedule_count`. Vì vậy trên state machine, hãy vẽ nó
như một **self-transition** (mũi tên vòng lại chính state `PENDING`/
`AWAITING_CONFIRMATION`/`CONFIRMED`), không phải một state riêng — chỉ được phép
khi state hiện tại thuộc 3 state active kể trên, và (nếu đang `CONFIRMED`) còn
`>= 6 giờ` tới giờ chơi hiện tại. Ràng buộc unique index vẫn áp dụng cho khung giờ
**mới** giống như khi tạo booking mới ở UC08.
