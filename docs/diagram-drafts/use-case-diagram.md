# Draft — Biểu đồ Use Case tổng quan

## Actor

- **Người chơi / Khách hàng** (Customer)
- **Chủ sân** (Field Owner)
- **Nhân viên sân** (Staff)
- **Quản trị viên hệ thống** (Admin)

## Actor — Use Case (association), theo 6 gói chức năng

| Gói | Actor | Use Case liên kết |
|---|---|---|
| G1 — Quản lý tài khoản | Người chơi, Chủ sân | UC01 (Đăng ký) |
| G1 | Người chơi, Chủ sân, Nhân viên, Quản trị viên | UC02 (Đăng nhập), UC03 (Đặt lại mật khẩu) |
| G1 | Người chơi, Chủ sân, Nhân viên | UC04 (Cập nhật thông tin cá nhân) |
| G2 — Tìm kiếm & Đặt sân | Người chơi | UC05, UC06, UC07, UC08, UC09, UC10, UC11, UC12 |
| G3 — Quản lý cơ sở sân | Chủ sân | UC13, UC14, UC15, UC16, UC17 |
| G4 — Vận hành sân | Nhân viên | UC18, UC19, UC20, UC21 |
| G5 — Đánh giá & phản hồi | Người chơi | UC22 |
| G5 | Chủ sân | UC23 |
| G6 — Quản trị hệ thống | Quản trị viên | UC24, UC25, UC26, UC27 |

Ghi chú: UC02 (Đăng nhập) và UC03 (Đặt lại mật khẩu) là use case dùng chung cho cả
4 actor — khi vẽ tay, vẽ 4 đường association riêng từ 4 actor tới cùng 1 hình elip.
UC04 chỉ dùng cho 3 actor tự thao tác trên tài khoản của mình (Người chơi/Chủ
sân/Nhân viên) — Quản trị viên không có nhu cầu nghiệp vụ riêng cho UC này trong
phạm vi đồ án (dù về kỹ thuật route `/profile` không chặn vai trò ADMIN).

## Quan hệ include / extend giữa các Use Case

### Chuỗi G2 (Tìm kiếm & Đặt sân) — chuỗi quan trọng nhất

- **UC08 «include» UC07** «include» **UC06** «include» **UC05**: để đặt được một
  khung giờ, Người chơi bắt buộc phải tìm sân (UC05) → xem chi tiết (UC06) → xem
  lịch trống (UC07) → đặt (UC08) — mỗi bước là tiền đề tất-yếu của bước sau, không
  thể bỏ qua.
- **UC09 «extend» UC08**: sau khi tạo booking (UC08) ở trạng thái `PENDING`, việc
  nộp minh chứng thanh toán (UC09) là một nhánh mở rộng có thể xảy ra sau đó (không
  bắt buộc xảy ra ngay — khách có thể để hết hạn), điểm mở rộng: "sau khi tạo
  booking PENDING".
- **UC18 «extend» UC09**: sau khi khách nộp minh chứng (UC09, chuyển
  `AWAITING_CONFIRMATION`), việc Nhân viên đối chiếu & xác nhận (UC18, thuộc G4) là
  một nhánh mở rộng xảy ra ở một actor khác — quan hệ extend liên gói (cross-package)
  thể hiện đúng việc G4 phụ thuộc vào dữ liệu do G2 tạo ra.
- **UC10 «extend» UC08** và **UC11 «extend» UC08**: hủy và đổi lịch là các nhánh
  thay thế có thể xảy ra sau khi đã có một booking — không phải bước bắt buộc,
  điểm mở rộng: "khi booking đang PENDING/AWAITING_CONFIRMATION/CONFIRMED".
- **UC12 độc lập**: xem lịch sử không include/extend UC nào — chỉ đọc dữ liệu do
  các UC khác tạo ra.

### Chuỗi G3 → G4 (thiết lập dữ liệu & vận hành)

- **UC14 «include» UC13**: phải có Cơ sở sân (UC13) trước khi thêm Sân/khung giờ
  vào cơ sở đó (UC14).
- **UC15 «extend» UC14**: sửa giá một khung giờ đã tồn tại là nhánh mở rộng của
  UC14 (không phải bước bắt buộc ngay khi tạo khung giờ mới).
- **UC20 «include» UC08**: Nhân viên đặt hộ khách vãng lai tái sử dụng đúng luồng
  tạo booking của UC08 (cùng service `create_booking`), chỉ khác actor kích hoạt.
- **UC18 «include» UC20** (nhánh tiền mặt): sau khi UC20 tạo booking `PENDING`,
  Nhân viên xác nhận thu tiền mặt ngay bằng UC18 (nhánh `confirm_cash_payment`,
  không cần qua UC09).
- **UC21 «include» UC10 + UC11**: xử lý đổi/hủy tại chỗ tái sử dụng đúng logic
  nghiệp vụ của UC10 (hủy) và UC11 (đổi lịch) — chỉ khác actor kích hoạt (Nhân viên
  thay Người chơi) và bối cảnh (yêu cầu phát sinh trực tiếp tại quầy).
- **UC16 độc lập với vòng đời booking**: là tiền đề dữ liệu (tạo tài khoản Nhân
  viên) cho UC18–UC21, không phải quan hệ include/extend theo đúng ngữ nghĩa UML.
- **UC17 độc lập**: chỉ đọc dữ liệu booking đã có, không include/extend UC nào.

### Chuỗi G5 (Đánh giá & phản hồi)

- **UC22 «extend» UC19**: đánh giá sân chỉ khả dụng sau khi một booking đã được
  Nhân viên check-in thành `COMPLETED` (UC19) — nhánh mở rộng xảy ra rất lâu sau đó
  (sau khi khách đã chơi xong), điểm mở rộng: "sau khi booking chuyển sang
  COMPLETED".
- **UC23 «extend» UC22**: phản hồi chỉ khả dụng sau khi đã có một đánh giá (UC22).

### Chuỗi G6 (Quản trị hệ thống)

- **UC24 «extend» UC13**: duyệt cơ sở sân mới là nhánh xử lý xảy ra sau khi Chủ sân
  đăng ký/gửi lại hồ sơ (UC13) — bắt buộc phải xảy ra trước khi UC05 (tìm sân) có
  thể trả về Sân thuộc cơ sở đó.
- **UC27 «extend» UC12**: Người chơi chỉ gửi khiếu nại được khi đã có ít nhất một
  booking (thường xem tại UC12/UC-lịch sử) — điểm mở rộng: "từ một booking đã
  CONFIRMED/COMPLETED".
- **UC25, UC26 độc lập**: không include/extend UC nào của actor khác — là các
  công cụ giám sát/quản trị xuyên suốt toàn hệ thống (đúng quan hệ "G6 phụ thuộc
  vào tất cả các gói còn lại" ở mức dữ liệu tổng hợp, không phải include/extend
  theo từng luồng cụ thể).

## Gợi ý bố cục khi vẽ tay

```
   [Người chơi]                    [Chủ sân]              [Nhân viên]        [Quản trị viên]
        |                               |                       |                    |
  ------+------------------      -------+-------          ------+------        -------+-------
  |  |  |  |  |  |  |  |  |      |   |   |   |   |         |   |   |   |        |   |   |   |
 UC05 UC08 UC10 UC12 UC22       UC13 UC16 UC17 UC23        UC18 UC20 UC21      UC24 UC25 UC26 UC27
  |include  ^         ^          |               ^          |    include        extend(UC13)
 UC06,UC07  |extend   |extend   UC14              |extend   |    UC08          extend(UC12)
      |include        (UC08)   |extend            (UC22)    |include(UC10,11)
     UC08                     UC15                          (UC21)

(UC02 Đăng nhập, UC03 Đặt lại mật khẩu: dùng chung cho cả 4 actor — vẽ 4 association
 riêng tới cùng 1 elip mỗi UC, không lặp lại trong sơ đồ trên cho gọn.
 UC04 Cập nhật thông tin: dùng chung cho Người chơi/Chủ sân/Nhân viên. UC01 Đăng ký:
 chỉ Người chơi/Chủ sân.)
```
