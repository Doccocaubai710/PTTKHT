# Tổng hợp chức năng theo Actor

> Tóm tắt các use case (UC01–UC27) mà mỗi actor có thể thực hiện, theo 6 gói chức
> năng G1–G6. Chi tiết đặc tả từng UC xem tại `docs/use-cases/`.

## Người chơi / Khách hàng (Customer)

| Gói | Chức năng |
|---|---|
| G1 | Đăng ký tài khoản (UC01); Đăng nhập (UC02); Đặt lại mật khẩu (UC03); Cập nhật thông tin cá nhân (UC04) |
| G2 | Tìm sân theo khu vực/loại thể thao (UC05); Xem chi tiết cơ sở/sân (UC06); Xem lịch trống theo khung giờ (UC07); Đặt sân (UC08); Nộp minh chứng chuyển khoản đặt cọc (UC09); Hủy đặt sân (UC10); Đổi lịch đặt sân (UC11); Xem lịch sử đặt sân (UC12) |
| G5 | Viết đánh giá sau khi hoàn tất sử dụng sân (UC22) |
| G6 | Gửi khiếu nại/tranh chấp liên quan tới một lượt đặt sân (UC27, phía gửi) |

## Chủ sân (Field Owner)

| Gói | Chức năng |
|---|---|
| G1 | Đăng ký tài khoản (UC01); Đăng nhập (UC02); Đặt lại mật khẩu (UC03); Cập nhật thông tin cá nhân (UC04) |
| G3 | Đăng ký/cập nhật cơ sở sân, gửi lại nếu bị từ chối (UC13); Quản lý sân và khung giờ (UC14); Thiết lập giá theo khung giờ (UC15); Tạo và khóa/mở tài khoản Nhân viên cho cơ sở của mình (UC16); Xem báo cáo doanh thu (UC17) |
| G5 | Xem và phản hồi đánh giá của khách hàng (UC23) |

## Nhân viên sân (Staff)

| Gói | Chức năng |
|---|---|
| G1 | Đăng nhập (UC02); Đặt lại mật khẩu (UC03); Cập nhật thông tin cá nhân (UC04) — **không** có form tự đăng ký (UC01), tài khoản do Chủ sân tạo ở UC16 |
| G4 | Xác nhận thanh toán đặt sân — đối chiếu minh chứng chuyển khoản hoặc thu tiền mặt (UC18); Check-in khách, đánh dấu hoàn tất sử dụng sân (UC19); Tạo đặt sân trực tiếp cho khách vãng lai (UC20); Xử lý yêu cầu đổi/hủy phát sinh tại chỗ (UC21) |

Mọi thao tác ở G4 chỉ giới hạn trong **một** Cơ sở sân mà Nhân viên được Chủ sân
gán vào (`User.facility_id`).

## Quản trị viên hệ thống (Admin)

| Gói | Chức năng |
|---|---|
| G1 | Đăng nhập (UC02); Đặt lại mật khẩu (UC03) — không có form tự đăng ký, tài khoản do hệ thống khởi tạo sẵn |
| G6 | Duyệt hoặc từ chối (kèm lý do) hồ sơ đăng ký cơ sở sân mới (UC24); Quản lý tài khoản người dùng toàn hệ thống — khóa/mở bất kỳ tài khoản nào, trừ tự khóa một Admin khác (UC25); Xem thống kê tổng quan hệ thống — người dùng theo vai trò, cơ sở theo trạng thái duyệt, đặt sân theo trạng thái, tổng doanh thu (UC26); Tiếp nhận và xử lý khiếu nại/tranh chấp do Người chơi gửi lên (UC27) |

## Bảng chéo Actor × Gói chức năng

| Gói | Người chơi | Chủ sân | Nhân viên | Quản trị viên |
|---|---|---|---|---|
| G1 — Quản lý tài khoản | ✅ (UC01-04) | ✅ (UC01-04) | ✅ (UC02-04, không UC01) | ✅ (UC02-03) |
| G2 — Tìm kiếm & Đặt sân | ✅ (UC05-12) | — | — | — |
| G3 — Quản lý cơ sở sân | — | ✅ (UC13-17) | — | — |
| G4 — Vận hành sân | — | — | ✅ (UC18-21) | — |
| G5 — Đánh giá & phản hồi | ✅ (UC22) | ✅ (UC23) | — | — |
| G6 — Quản trị hệ thống | ✅ (UC27, gửi) | — | — | ✅ (UC24-27) |
