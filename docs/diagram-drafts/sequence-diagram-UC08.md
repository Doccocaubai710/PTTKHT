# Draft — Sequence Diagram cho UC08 (Đặt sân)

## Luồng chính (thành công)

```
1.  Người chơi -> FieldDetailPage.book_slot(slot_id)
2.  FieldDetailPage -> BookingService.create_booking(field_id, time_slot_id, booking_date, customer_id, created_by_id)
3.  BookingService -> BookingService: kiểm tra booking_date >= today
4.  BookingService -> FieldTimeSlotRepository.get_by_id(session, time_slot_id) : slot
5.  FieldTimeSlotRepository -> Database: SELECT ... FROM field_time_slots WHERE id = ?
6.  Database --> FieldTimeSlotRepository: slot (start_time, end_time, price, is_active)
7.  FieldTimeSlotRepository --> BookingService: slot
8.  BookingService -> BookingService: total_price = slot.price; deposit = total_price * 0.3
9.  BookingService -> BookingRepository.add(session, booking mới với status=PENDING)
10. BookingRepository -> Database: INSERT INTO bookings (...) VALUES (...)
11. Database -> Database: kiểm tra partial UNIQUE INDEX (field_id, booking_date, time_slot_id) WHERE status IN (PENDING, AWAITING_CONFIRMATION, CONFIRMED, COMPLETED)
12. Database --> BookingRepository: OK (không vi phạm ràng buộc)
13. BookingRepository --> BookingService: booking (đã có id)
14. BookingService -> Database: COMMIT transaction
15. BookingService --> FieldDetailPage: booking (status=PENDING, hold_expires_at=now+10p)
16. FieldDetailPage --> Người chơi: thông báo "Đặt sân thành công, vui lòng thanh toán cọc" + điều hướng "/my-bookings"
```

## Luồng ngoại lệ A1 — Trùng lịch (2 khách đặt cùng lúc)

```
1.  Người chơi A -> FieldDetailPage.book_slot(slot_id)
2.  FieldDetailPage -> BookingService.create_booking(...)
3.  BookingService -> BookingRepository.add(session, booking A với status=PENDING)
4.  BookingRepository -> Database: INSERT booking A

    (song song, gần như cùng thời điểm)
4'. Người chơi B -> FieldDetailPage.book_slot(slot_id)  [cùng field_id, cùng ngày, cùng time_slot_id]
5'. FieldDetailPage -> BookingService.create_booking(...)
6'. BookingService -> BookingRepository.add(session, booking B với status=PENDING)
7'. BookingRepository -> Database: INSERT booking B

8.  Database -> Database: transaction của A COMMIT trước -> ràng buộc UNIQUE thỏa mãn -> ghi thành công
9.  Database --> BookingRepository (của A): OK
10. BookingService (A) --> FieldDetailPage (A): booking thành công

11. Database -> Database: transaction của B cố COMMIT -> vi phạm partial UNIQUE INDEX
                          (đã tồn tại 1 bản ghi active cho đúng field_id+date+slot_id)
12. Database --> BookingRepository (của B): raise IntegrityError
13. BookingRepository --> BookingService (B): propagate IntegrityError
14. BookingService -> BookingService: catch IntegrityError -> session.rollback()
15. BookingService -> BookingService: raise BookingError("Khung giờ đã được đặt, vui lòng chọn khung giờ khác.")
16. BookingService --> FieldDetailPage (B): BookingError
17. FieldDetailPage --> Người chơi B: hiển thị thông báo lỗi nghiệp vụ (ui.notify, type=negative)
```

## Ghi chú

- Bước 8/11 ở luồng ngoại lệ là điểm mấu chốt: **DBMS** (không phải code Python) là
  nơi thực sự phân xử ai đặt được trước, vì INSERT+kiểm-tra-ràng-buộc là một thao
  tác nguyên tử (atomic) tại tầng lưu trữ — loại bỏ hoàn toàn khoảng hở
  race-condition mà một cách làm "SELECT kiểm tra trước rồi mới INSERT" ở tầng
  ứng dụng sẽ mắc phải.
- `BookingRepository.add()` gọi `session.flush()` (không phải chỉ `session.add()`)
  để buộc SQLAlchemy gửi câu lệnh INSERT tới CSDL ngay, giúp bắt được
  `IntegrityError` ngay tại đó thay vì trì hoãn tới lúc commit cuối transaction.
