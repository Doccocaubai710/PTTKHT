# Draft — Sequence Diagram cho UC004 (Thanh toán đặt cọc - mock)

## Luồng chính (thành công)

```
1. Khách hàng -> MyBookingsPage.pay(booking_id)
2. MyBookingsPage -> BookingService.pay_deposit(booking_id, payment_method="MOCK_ONLINE")
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking
4. BookingRepository -> Database: SELECT * FROM bookings WHERE id = ?
5. Database --> BookingRepository: booking (status=PENDING, hold_expires_at=...)
6. BookingRepository --> BookingService: booking
7. BookingService -> BookingService: kiểm tra now <= booking.hold_expires_at (chưa hết hạn giữ chỗ)
8. BookingService -> BookingService: validate_transition(PENDING, CONFIRMED) -> hợp lệ
9. BookingService -> MockPaymentGateway: charge(deposit_amount)  «mock, luôn thành công»
10. MockPaymentGateway --> BookingService: True
11. BookingService -> BookingService: booking.is_deposit_paid = True; booking.payment_method = "MOCK_ONLINE"; booking.status = CONFIRMED
12. BookingService -> Database: session.flush() / COMMIT
13. BookingService --> MyBookingsPage: booking (status=CONFIRMED)
14. MyBookingsPage --> Khách hàng: thông báo "Thanh toán cọc thành công (mô phỏng)." + làm mới danh sách
```

## Luồng ngoại lệ A1 — Quá thời gian giữ chỗ

```
1. Khách hàng -> MyBookingsPage.pay(booking_id)
2. MyBookingsPage -> BookingService.pay_deposit(booking_id)
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking
4. BookingService -> BookingService: kiểm tra now > booking.hold_expires_at (đã quá 10 phút)
5. BookingService -> BookingService: _expire(booking) -> validate_transition(PENDING, EXPIRED) -> booking.status = EXPIRED
6. BookingService -> Database: session.flush() (lưu trạng thái EXPIRED)
7. BookingService -> BookingService: raise BookingError("Đã quá thời gian giữ chỗ, vui lòng đặt lại khung giờ khác.")
8. BookingService --> MyBookingsPage: BookingError
9. MyBookingsPage --> Khách hàng: hiển thị thông báo lỗi (ui.notify, type=negative)
```

## Luồng ngoại lệ A2 — Booking không ở trạng thái PENDING

```
1. Khách hàng -> MyBookingsPage.pay(booking_id)   [booking đã CONFIRMED từ trước, VD double-click]
2. MyBookingsPage -> BookingService.pay_deposit(booking_id)
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking (status=CONFIRMED)
4. BookingService -> BookingService: validate_transition(CONFIRMED, CONFIRMED) -> không có trong ALLOWED_TRANSITIONS
5. BookingService -> BookingService: raise BookingError("Không thể chuyển trạng thái đặt sân từ CONFIRMED sang CONFIRMED.")
6. BookingService --> MyBookingsPage: BookingError
7. MyBookingsPage --> Khách hàng: hiển thị thông báo lỗi
```
