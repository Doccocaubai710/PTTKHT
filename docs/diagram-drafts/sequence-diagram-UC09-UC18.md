# Draft — Sequence Diagram cho UC09 + UC18 (Thanh toán đặt cọc & Xác nhận thanh toán)

## Luồng chính — UC09: Người chơi nộp minh chứng chuyển khoản

```
1. Người chơi -> MyBookingsPage.submit_proof_dialog(booking_id)
2. MyBookingsPage --> Người chơi: hiển thị mã QR/thông tin chuyển khoản + form nhập mã giao dịch
3. Người chơi -> MyBookingsPage.submit(proof_ref)
4. MyBookingsPage -> BookingService.submit_payment_proof(booking_id, customer_id, proof_ref)
5. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking
6. BookingService -> BookingService: kiểm tra booking.customer_id == customer_id
7. BookingService -> BookingService: kiểm tra now <= booking.hold_expires_at (chưa hết hạn giữ chỗ)
8. BookingService -> BookingService: validate_transition(PENDING, AWAITING_CONFIRMATION) -> hợp lệ
9. BookingService -> BookingService: booking.payment_proof_ref = proof_ref; booking.payment_method = "ONLINE_QR"; booking.status = AWAITING_CONFIRMATION
10. BookingService -> Database: session.flush() / COMMIT
11. BookingService --> MyBookingsPage: booking (status=AWAITING_CONFIRMATION)
12. MyBookingsPage --> Người chơi: thông báo "Đã gửi minh chứng, chờ nhân viên xác nhận."
```

## Luồng chính — UC18 (nhánh khớp): Nhân viên xác nhận giao dịch chuyển khoản

```
1. Nhân viên -> StaffTodayPage.confirm_online(booking_id)   [sau khi đã đối chiếu thủ công với app ngân hàng]
2. StaffTodayPage -> BookingService.confirm_payment(booking_id, staff_id)
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking (status=AWAITING_CONFIRMATION)
4. BookingService -> BookingService: validate_transition(AWAITING_CONFIRMATION, CONFIRMED) -> hợp lệ
5. BookingService -> BookingService: booking.is_deposit_paid = True; booking.status = CONFIRMED; booking.confirmed_by_id = staff_id
6. BookingService -> Database: session.flush() / COMMIT
7. BookingService --> StaffTodayPage: booking (status=CONFIRMED)
8. StaffTodayPage --> Nhân viên: thông báo "Đã xác nhận giao dịch chuyển khoản."
```

## Luồng chính — UC18 (nhánh tiền mặt): Nhân viên xác nhận thu tiền mặt tại quầy

```
1. Nhân viên -> StaffTodayPage.confirm_cash(booking_id)   [booking đang PENDING, khách trả tiền mặt trực tiếp]
2. StaffTodayPage -> BookingService.confirm_cash_payment(booking_id, staff_id)
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking (status=PENDING)
4. BookingService -> BookingService: validate_transition(PENDING, CONFIRMED) -> hợp lệ
5. BookingService -> BookingService: booking.payment_method = "CASH"; booking.status = CONFIRMED; booking.confirmed_by_id = staff_id
6. BookingService -> Database: session.flush() / COMMIT
7. BookingService --> StaffTodayPage: booking (status=CONFIRMED)
8. StaffTodayPage --> Nhân viên: thông báo "Đã xác nhận thanh toán tiền mặt."
```

## Luồng ngoại lệ A1 — UC18: Không khớp minh chứng, nhân viên từ chối

```
1. Nhân viên -> StaffTodayPage.reject_dialog(booking_id)
2. StaffTodayPage --> Nhân viên: hiển thị form nhập lý do từ chối
3. Nhân viên -> StaffTodayPage.submit(reason)
4. StaffTodayPage -> BookingService.reject_payment(booking_id, staff_id, reason)
5. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking (status=AWAITING_CONFIRMATION)
6. BookingService -> BookingService: validate_transition(AWAITING_CONFIRMATION, PENDING) -> hợp lệ
7. BookingService -> BookingService: booking.status = PENDING; booking.payment_rejected_reason = reason; booking.hold_expires_at = now + 10 phút (gia hạn)
8. BookingService -> Database: session.flush() / COMMIT
9. BookingService --> StaffTodayPage: booking (status=PENDING)
10. StaffTodayPage --> Nhân viên: thông báo "Đã từ chối, khách cần bổ sung minh chứng khác."

    (sau đó, ở phiên của Người chơi)
11. Người chơi -> MyBookingsPage: mở "/my-bookings", thấy booking quay lại PENDING kèm payment_rejected_reason
12. Người chơi -> (lặp lại luồng UC09 ở trên với minh chứng mới)
```

## Luồng ngoại lệ A2 — UC09: Quá thời gian giữ chỗ trước khi nộp minh chứng

```
1. Người chơi -> MyBookingsPage.submit_proof_dialog(booking_id)
2. MyBookingsPage -> BookingService.submit_payment_proof(booking_id, customer_id, proof_ref)
3. BookingService -> BookingRepository.get_by_id(session, booking_id) : booking
4. BookingService -> BookingService: kiểm tra now > booking.hold_expires_at (đã quá 10 phút) -> THẤT BẠI
5. BookingService -> BookingService: _expire(booking) -> validate_transition(PENDING, EXPIRED) -> booking.status = EXPIRED
6. BookingService -> Database: session.flush() (lưu trạng thái EXPIRED)
7. BookingService -> BookingService: raise BookingError("Đã quá thời gian giữ chỗ, vui lòng đặt lại khung giờ khác.")
8. BookingService --> MyBookingsPage: BookingError
9. MyBookingsPage --> Người chơi: hiển thị thông báo lỗi (ui.notify, type=negative)
```

## Ghi chú

- UC09 và UC18 luôn xảy ra ở hai phiên làm việc (session) khác nhau — Người chơi và
  Nhân viên không tương tác trực tiếp qua hệ thống trong lúc thực hiện, chỉ gặp
  nhau qua trạng thái chung của cùng một bản ghi `Booking`. Khi vẽ sequence diagram
  cho báo cáo, nên tách rõ 2 "lifeline" thời gian (có thể cách nhau vài phút tới vài
  giờ) để tránh gây hiểu nhầm là đồng bộ (synchronous) như một lời gọi hàm thông
  thường.
