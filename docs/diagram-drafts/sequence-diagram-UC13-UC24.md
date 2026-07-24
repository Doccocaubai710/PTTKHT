# Draft — Sequence Diagram cho UC13 + UC24 (Đăng ký & Duyệt cơ sở sân mới)

## Luồng chính — UC13: Chủ sân đăng ký cơ sở sân mới

```
1. Chủ sân -> OwnerDashboardPage.new_facility_dialog()
2. OwnerDashboardPage --> Chủ sân: hiển thị form (Tên cơ sở, Khu vực, Địa chỉ, Mô tả, Chính sách hủy/đổi lịch)
3. Chủ sân -> OwnerDashboardPage.submit()
4. OwnerDashboardPage -> FacilityService.register_facility(owner_id, name, area, address, description, policy)
5. FacilityService -> FacilityService: validate name/area/address không rỗng
6. FacilityService -> FacilityRepository.add(session, facility mới với status=PENDING)
7. FacilityRepository -> Database: INSERT INTO facilities (...) VALUES (...)
8. Database --> FacilityRepository: facility (đã có id)
9. FacilityRepository --> FacilityService: facility
10. FacilityService --> OwnerDashboardPage: facility (status=PENDING)
11. OwnerDashboardPage --> Chủ sân: thông báo "Đã gửi hồ sơ đăng ký, chờ Quản trị viên duyệt."

    (Chủ sân tiếp tục UC14/UC15 thêm Sân/khung giờ cho facility này —
     các Sân này chưa xuất hiện trong tìm kiếm UC05 của Người chơi)
```

## Luồng chính — UC24: Quản trị viên duyệt cơ sở sân

```
1. Quản trị viên -> AdminFacilitiesPage: mở "/admin"
2. AdminFacilitiesPage -> FacilityService.list_pending_facilities()
3. FacilityService -> FacilityRepository.list_by_status(session, PENDING) : facilities
4. FacilityRepository -> Database: SELECT * FROM facilities WHERE status = 'PENDING'
5. Database --> FacilityRepository: facilities
6. FacilityRepository --> FacilityService: facilities
7. FacilityService --> AdminFacilitiesPage: facilities
8. AdminFacilitiesPage --> Quản trị viên: hiển thị danh sách kèm tên/khu vực/địa chỉ/mô tả

9. Quản trị viên -> AdminFacilitiesPage.approve(facility_id)
10. AdminFacilitiesPage -> FacilityService.approve_facility(facility_id, admin_id)
11. FacilityService -> FacilityRepository.get_by_id(session, facility_id) : facility
12. FacilityService -> FacilityService: kiểm tra facility.status == PENDING -> hợp lệ
13. FacilityService -> FacilityService: facility.status = APPROVED; facility.reviewed_by_id = admin_id; facility.reviewed_at = now
14. FacilityService -> Database: session.flush() / COMMIT
15. FacilityService --> AdminFacilitiesPage: facility (status=APPROVED)
16. AdminFacilitiesPage --> Quản trị viên: thông báo "Đã duyệt, cơ sở sân được hiển thị công khai."

    (từ lúc này, FieldRepository.search(..., approved_only=True) ở UC05
     sẽ trả về các Sân thuộc facility này cho mọi Người chơi)
```

## Luồng ngoại lệ A1 — Quản trị viên từ chối hồ sơ

```
1. Quản trị viên -> AdminFacilitiesPage.reject_dialog(facility_id)
2. AdminFacilitiesPage --> Quản trị viên: hiển thị form nhập lý do từ chối
3. Quản trị viên -> AdminFacilitiesPage.submit(reason)
4. AdminFacilitiesPage -> FacilityService.reject_facility(facility_id, admin_id, reason)
5. FacilityService -> FacilityRepository.get_by_id(session, facility_id) : facility
6. FacilityService -> FacilityService: kiểm tra facility.status == PENDING -> hợp lệ
7. FacilityService -> FacilityService: facility.status = REJECTED; facility.reject_reason = reason; facility.reviewed_by_id = admin_id; facility.reviewed_at = now
8. FacilityService -> Database: session.flush() / COMMIT
9. FacilityService --> AdminFacilitiesPage: facility (status=REJECTED)
10. AdminFacilitiesPage --> Quản trị viên: thông báo "Đã từ chối hồ sơ."

    (sau đó, ở phiên của Chủ sân — luồng UC13 "Chỉnh sửa & gửi lại")
11. Chủ sân -> OwnerDashboardPage: mở "/owner", thấy facility ở trạng thái "Bị từ chối" kèm reject_reason
12. Chủ sân -> OwnerDashboardPage.edit_facility_dialog(facility)
13. Chủ sân -> OwnerDashboardPage.submit() [đã sửa thông tin theo góp ý]
14. OwnerDashboardPage -> FacilityService.update_facility(facility_id, owner_id, name, area, address, description, policy)
15. FacilityService -> FacilityService: facility.status == REJECTED -> tự chuyển lại status = PENDING; xóa reject_reason
16. FacilityService -> Database: session.flush() / COMMIT
17. FacilityService --> OwnerDashboardPage: facility (status=PENDING)
18. OwnerDashboardPage --> Chủ sân: thông báo "Đã gửi lại hồ sơ để duyệt." (quay lại hàng chờ của UC24)
```

## Luồng ngoại lệ A2 — Cơ sở không còn ở trạng thái chờ duyệt (double-click / xử lý trùng)

```
1. Quản trị viên -> AdminFacilitiesPage.approve(facility_id)   [đã được một Quản trị viên khác duyệt/từ chối trước đó]
2. AdminFacilitiesPage -> FacilityService.approve_facility(facility_id, admin_id)
3. FacilityService -> FacilityRepository.get_by_id(session, facility_id) : facility (status=APPROVED, không còn PENDING)
4. FacilityService -> FacilityService: kiểm tra facility.status == PENDING -> THẤT BẠI
5. FacilityService -> FacilityService: raise FacilityError("Cơ sở sân này không ở trạng thái chờ duyệt.")
6. FacilityService --> AdminFacilitiesPage: FacilityError
7. AdminFacilitiesPage --> Quản trị viên: hiển thị thông báo lỗi
```
