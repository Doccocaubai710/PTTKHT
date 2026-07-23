# Draft — Biểu đồ Use Case tổng quan

## Actor

- **Khách hàng** (Customer)
- **Chủ sân** (Field Owner)
- **Nhân viên** (Staff)

## Actor — Use Case (association)

| Actor | Use Case liên kết |
|---|---|
| Khách hàng | UC001 (Đăng ký/Đăng nhập), UC002 (Tìm sân), UC003 (Đặt sân), UC004 (Thanh toán cọc), UC005 (Hủy đặt sân), UC008 (Đánh giá sân) |
| Chủ sân | UC001 (Đăng ký/Đăng nhập), UC006 (Quản lý khung giờ & giá sân) |
| Nhân viên | UC001 (Đăng ký/Đăng nhập), UC007 (Đặt hộ khách walk-in) |

Ghi chú: UC001 là use case dùng chung cho cả 3 actor (mỗi actor đăng ký/đăng nhập
với vai trò khác nhau) — khi vẽ tay, có thể vẽ 3 đường association riêng từ 3 actor
tới cùng 1 hình elip UC001.

## Quan hệ include / extend giữa các Use Case

- **UC003 «include» UC002**: để đặt được một khung giờ, Khách hàng bắt buộc phải đi
  qua bước tìm/xem khung giờ trống trước (UC002 là một phần tất-yếu của luồng dẫn
  tới UC003, không thể bỏ qua).
- **UC003 «include» UC001** (gián tiếp qua tiền điều kiện "đã đăng nhập"): mọi UC
  của Khách hàng/Chủ sân/Nhân viên đều yêu cầu đã đăng nhập; khi vẽ tay có thể chỉ
  vẽ include từ UC003/UC006/UC007 (các UC có tạo/sửa dữ liệu) để tránh rối hình,
  hoặc vẽ 1 include chung từ một UC "Xác thực phiên" bao trùm.
- **UC004 «extend» UC003**: sau khi tạo booking (UC003) ở trạng thái PENDING, việc
  thanh toán cọc (UC004) là một nhánh mở rộng có thể xảy ra sau đó (không bắt buộc
  xảy ra ngay — khách có thể chưa thanh toán và để hết hạn), nên dùng quan hệ
  «extend» (điểm mở rộng: "sau khi tạo booking PENDING") thay vì «include».
- **UC005 «extend» UC003**: hủy đặt sân là một nhánh thay thế có thể xảy ra sau khi
  đã có một booking (dù đã hay chưa thanh toán cọc) — không phải bước bắt buộc của
  luồng chính, nên là «extend», điểm mở rộng: "khi booking đang PENDING hoặc
  CONFIRMED".
- **UC007 «include» UC003 + UC004**: nhân viên đặt hộ khách walk-in thực chất tái sử
  dụng đúng luồng tạo booking (UC003) và có thể thực hiện luôn xác nhận thanh toán
  (UC004, nhưng với hình thức CASH thay vì MOCK_ONLINE) — nên UC007 «include» cả
  hai, chỉ khác actor kích hoạt và hình thức thanh toán.
- **UC008 «extend» UC007 / hoàn tất sử dụng sân**: đánh giá sân chỉ khả dụng sau khi
  một booking đã được Nhân viên check-in thành COMPLETED (xảy ra trong luồng
  UC007) — đây là nhánh mở rộng xảy ra rất lâu sau đó (sau khi khách đã chơi xong),
  điểm mở rộng: "sau khi booking chuyển sang COMPLETED".
- **UC006 độc lập**: không có quan hệ include/extend với các UC khác — Chủ sân thiết
  lập dữ liệu (sân, khung giờ, giá) trước, độc lập với vòng đời của từng booking cụ
  thể; đây là **tiền điều kiện dữ liệu** cho UC002/UC003 chứ không phải quan hệ
  include/extend theo đúng ngữ nghĩa UML (include/extend là quan hệ giữa các UC
  trong cùng một luồng thực thi, không phải quan hệ "dữ liệu tiền đề").

## Gợi ý bố cục khi vẽ tay

```
        [Khách hàng]                         [Chủ sân]        [Nhân viên]
             |                                    |                |
   -----------------------              (UC001)==========(UC001)===(UC001)
   |    |    |    |   |   |                        |                |
 UC001 UC002 UC003 UC005 UC008                    UC006            UC007
             |  ^        ^                                          | include
        include|         | extend                              ----+----
             UC002    (từ UC003)                                UC003 UC004
             |
        extend (UC004, từ UC003)
```
