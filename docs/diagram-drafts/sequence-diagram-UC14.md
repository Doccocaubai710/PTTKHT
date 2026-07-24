# Draft — Sequence Diagram cho UC14 (Quản lý sân và khung giờ)

## Luồng chính A — Thêm sân mới vào một Cơ sở sân đã có (UC13 là tiền đề)

```
1. Chủ sân -> OwnerDashboardPage.new_field_dialog(facility_id)
2. OwnerDashboardPage --> Chủ sân: hiển thị form (Tên sân, Loại sân, Mô tả)
3. Chủ sân -> OwnerDashboardPage.submit()
4. OwnerDashboardPage -> FieldService.create_field(owner_id, facility_id, name, sport_type, description)
5. FieldService -> FacilityRepository.get_by_id(session, facility_id) : facility
6. FieldService -> FieldService: kiểm tra facility.owner_id == owner_id -> hợp lệ
7. FieldService -> FieldService: validate name không rỗng
8. FieldService -> FieldRepository.add(session, field mới với facility_id)
9. FieldRepository -> Database: INSERT INTO fields (...) VALUES (...)
10. Database --> FieldRepository: field (đã có id)
11. FieldRepository --> FieldService: field
12. FieldService --> OwnerDashboardPage: field
13. OwnerDashboardPage -> OwnerDashboardPage: refresh() (nạp lại danh sách sân)
14. OwnerDashboardPage --> Chủ sân: thông báo "Đã thêm sân mới."
```

## Luồng ngoại lệ A0 — Cơ sở sân không thuộc quyền sở hữu của Chủ sân

```
1. Chủ sân -> OwnerDashboardPage.submit()   [facility_id không thuộc owner_id hiện tại]
2. OwnerDashboardPage -> FieldService.create_field(owner_id, facility_id, ...)
3. FieldService -> FacilityRepository.get_by_id(session, facility_id) : facility
4. FieldService -> FieldService: kiểm tra facility.owner_id == owner_id -> THẤT BẠI
5. FieldService -> FieldService: raise FieldError("Cơ sở sân không hợp lệ.")
6. FieldService --> OwnerDashboardPage: FieldError
7. OwnerDashboardPage --> Chủ sân: hiển thị thông báo lỗi, không có sân nào được tạo
```

## Luồng chính B — Thêm khung giờ mới cho một sân

```
1. Chủ sân -> OwnerDashboardPage.add_slot(field_id, start_time, end_time, price)
2. OwnerDashboardPage -> FieldService.add_time_slot(field_id, start_time, end_time, price)
3. FieldService -> FieldService: validate start_time < end_time
4. FieldService -> FieldService: validate price > 0
5. FieldService -> FieldTimeSlotRepository.add(session, slot mới với is_active=True)
6. FieldTimeSlotRepository -> Database: INSERT INTO field_time_slots (...) VALUES (...)
7. Database --> FieldTimeSlotRepository: slot (đã có id)
8. FieldTimeSlotRepository --> FieldService: slot
9. FieldService --> OwnerDashboardPage: slot
10. OwnerDashboardPage -> OwnerDashboardPage: refresh()
11. OwnerDashboardPage --> Chủ sân: thông báo "Đã thêm khung giờ mới."
```

## Luồng chính C — Sửa giá / bật-tắt khung giờ

```
1. Chủ sân -> OwnerDashboardPage.save_price(slot_id, new_price)
2. OwnerDashboardPage -> FieldService.update_time_slot_price(slot_id, new_price)
3. FieldService -> FieldService: validate new_price > 0
4. FieldService -> FieldTimeSlotRepository.get_by_id(session, slot_id) : slot
5. FieldService -> FieldService: slot.price = new_price
6. FieldService -> Database: session.flush() / COMMIT (qua get_session() context)
7. FieldService --> OwnerDashboardPage: (không trả dữ liệu, cập nhật thành công)
8. OwnerDashboardPage --> Chủ sân: thông báo "Đã cập nhật giá."

--- tương tự cho bật/tắt khung giờ ---
1'. Chủ sân -> OwnerDashboardPage.toggle_active(slot_id, is_active)
2'. OwnerDashboardPage -> FieldService.set_time_slot_active(slot_id, is_active)
3'. FieldService -> FieldTimeSlotRepository.get_by_id(session, slot_id) : slot
4'. FieldService -> FieldService: slot.is_active = is_active
5'. FieldService -> Database: session.flush() / COMMIT
6'. FieldService --> OwnerDashboardPage: (thành công)
7'. OwnerDashboardPage --> Chủ sân: thông báo "Đã cập nhật trạng thái khung giờ."
```

## Luồng ngoại lệ A1 — Giờ bắt đầu ≥ giờ kết thúc

```
1. Chủ sân -> OwnerDashboardPage.add_slot(field_id, start_time="08:00", end_time="07:00", price)
2. OwnerDashboardPage -> FieldService.add_time_slot(...)
3. FieldService -> FieldService: validate start_time < end_time -> THẤT BẠI
4. FieldService -> FieldService: raise FieldError("Giờ bắt đầu phải trước giờ kết thúc.")
5. FieldService --> OwnerDashboardPage: FieldError
6. OwnerDashboardPage --> Chủ sân: hiển thị thông báo lỗi, không có khung giờ nào được tạo
```
