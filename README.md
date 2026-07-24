# Hệ thống đặt sân thể thao (PTTKHT)

Đồ án môn Phân tích thiết kế hệ thống — nền tảng web đặt sân thể thao (bóng đá mini,
cầu lông, tennis) phục vụ 4 nhóm actor: **Người chơi** (tìm & đặt sân online),
**Chủ sân** (đăng ký cơ sở, quản lý sân/giá/nhân viên, xem doanh thu), **Nhân viên
sân** (vận hành tại quầy: xác nhận thanh toán, check-in, đặt hộ khách vãng lai) và
**Quản trị viên hệ thống** (duyệt cơ sở mới, quản lý tài khoản toàn hệ thống, thống
kê, xử lý khiếu nại).

Triển khai đầy đủ 27 use case (UC01–UC27), chia thành 6 gói chức năng G1–G6 —
xem chi tiết từng use case tại `docs/use-cases/` và tóm tắt theo actor tại
`docs/actor_function.md`.

> Đây là bản demo phục vụ luồng nghiệp vụ + là cơ sở để vẽ tay các sơ đồ UML (xem
> thư mục `docs/`). Cổng thanh toán, SMS/email đều được **mock** — không gọi dịch
> vụ bên ngoài thật; bước "xác nhận giao dịch chuyển khoản" được thay bằng đối
> chiếu thủ công của Nhân viên sân, đúng theo luồng nghiệp vụ mô tả trong đề bài.

## Tech stack

- **Ngôn ngữ:** Python 3.11
- **Backend / UI:** [NiceGUI](https://nicegui.io) (xây trên FastAPI + Starlette) —
  giao diện web render từ Python, nút bấm gọi thẳng hàm Python qua WebSocket, không
  cần viết riêng frontend JavaScript/React.
- **ORM / Data access:** SQLAlchemy 2.x
- **Database:** SQLite (file, không cần cài DB server)
- **Auth:** JWT (PyJWT) phát hành khi đăng nhập, lưu trong session trình duyệt
  (`app.storage.user`), kiểm tra lại ở mỗi trang được bảo vệ theo role
  (`CUSTOMER` / `FIELD_OWNER` / `STAFF` / `ADMIN`)
- **Mật khẩu:** bcrypt

## Cấu trúc thư mục

```
/src/app
  /core         Cấu hình, kết nối DB (SQLAlchemy), bảo mật (JWT/bcrypt)
  /models       Entity: User, Facility, Field, FieldTimeSlot, Booking, Review,
                Complaint, PasswordResetToken, enums (UserRole, SportType,
                FacilityStatus, BookingStatus, ComplaintStatus)
  /repositories Data Access layer (CRUD thuần, không chứa business rule)
  /services     Business Logic layer: auth, facility, field, staff, booking,
                review, complaint, admin
  /pages        Presentation layer: các trang NiceGUI (@ui.page), 1 module/role
                (auth_pages, customer_pages, owner_pages, staff_pages,
                admin_pages) + guards.py (route guard theo JWT/role)
  main.py       Entry point, đăng ký route + job tự động hết hạn booking
  seed.py       Script tạo dữ liệu mẫu
/docs
  use-cases/         Đặc tả chi tiết 27 Use Case (UC01.md ... UC27.md)
  actor_function.md  Tóm tắt chức năng theo từng actor + bảng chéo Actor × Gói
  diagram-drafts/    Draft text cho package/use-case/class/sequence/state diagram
  architecture.md    Kiến trúc hệ thống + design pattern đã áp dụng
```

## Cài đặt

Yêu cầu: đã cài **conda** (Miniconda/Anaconda).

```bash
# 1. Tạo môi trường conda
conda create -y -n sportbook python=3.11
conda activate sportbook

# 2. Cài dependencies
pip install -r requirements.txt
```

## Khởi tạo dữ liệu mẫu

```bash
cd src
python -m app.seed
```

Lệnh này tạo file SQLite tại `data/sportbook.db` và seed:
- 2 cơ sở sân: "Khu liên hợp thể thao Thắng Lợi" (Cầu Giấy, đã được duyệt — gồm 1
  sân bóng đá mini) và "Cụm sân cầu lông - tennis Ánh Sáng" (Thanh Xuân, **đang chờ
  duyệt** — minh họa UC24, gồm 1 sân cầu lông + 1 sân tennis), mỗi sân 5 khung giờ
  (sáng sớm + tối)
- 4 tài khoản demo (mật khẩu đều là `123456`):

| Vai trò | Số điện thoại | Mật khẩu |
|---|---|---|
| Khách hàng | 0900000002 | 123456 |
| Chủ sân | 0900000001 | 123456 |
| Nhân viên (thuộc cơ sở Cầu Giấy) | 0900000003 | 123456 |
| Quản trị viên | 0900000004 | 123456 |

Chạy lại `python -m app.seed` khi đã có dữ liệu sẽ tự bỏ qua (không tạo trùng).

## Chạy ứng dụng

```bash
cd src
python -m app.main
```

Mở trình duyệt tại **http://localhost:8090/login**.

Ứng dụng cũng chạy một job nền kiểm tra mỗi 30 giây để tự động chuyển các lượt đặt
sân `PENDING`/`AWAITING_CONFIRMATION` quá 10 phút chưa được xác nhận thanh toán
sang `EXPIRED` (theo state machine ở `docs/diagram-drafts/state-machine-booking.md`).

## Luồng demo nhanh theo từng UC

1. Đăng nhập tài khoản Quản trị viên → **Duyệt cơ sở** → duyệt cơ sở "Cụm sân cầu
   lông - tennis Ánh Sáng" đang chờ (UC24) để các sân trong đó xuất hiện khi tìm
   kiếm.
2. Đăng xuất, đăng nhập tài khoản Khách hàng → **Tìm sân** → chọn sân → chọn
   ngày/khung giờ trống → **Đặt khung giờ này** (UC05–UC08).
3. Vào **Đặt sân của tôi** → **Nộp minh chứng** (nhập mã giao dịch bất kỳ, mock) để
   chuyển `PENDING` → `AWAITING_CONFIRMATION` (UC09); hoặc **Hủy**/**Đổi lịch** để
   xem chính sách hoàn cọc/đổi khung giờ (UC10–UC11).
4. Đăng xuất, đăng nhập tài khoản Nhân viên → **Đặt sân hôm nay** → **Xác nhận
   khớp** để chuyển sang `CONFIRMED` (UC18); hoặc sang tab **Đặt hộ khách** để tạo
   đặt sân walk-in cho khách vãng lai (UC20).
5. Nhân viên bấm **Check-in / hoàn tất** (booking chuyển `COMPLETED`, UC19) →
   đăng nhập lại tài khoản Khách hàng tương ứng để **Đánh giá sân** (UC22).
6. Đăng nhập tài khoản Chủ sân → **Cơ sở & sân của tôi** để đăng ký cơ sở mới/thêm
   sân, khung giờ, sửa giá (UC13–UC15); **Nhân viên** để tạo/khóa tài khoản nhân
   viên (UC16); **Doanh thu** để xem báo cáo (UC17); **Đánh giá** để phản hồi đánh
   giá của khách (UC23).
7. Từ trang **Đặt sân của tôi** hoặc **Khiếu nại của tôi** (Khách hàng), gửi một
   khiếu nại (UC27) → đăng nhập Quản trị viên, vào **Khiếu nại** để xử lý; vào
   **Tài khoản**/**Thống kê** để quản lý tài khoản toàn hệ thống (UC25) và xem số
   liệu tổng quan (UC26).

Mọi actor đều có trang **Tài khoản** (`/profile`) để đổi thông tin cá nhân/mật khẩu
(UC04) và trang **Quên mật khẩu** ở màn đăng nhập (UC03).

## Yêu cầu kỹ thuật trọng tâm đã triển khai

- **Chống trùng lịch:** partial unique index trên `(field_id, booking_date,
  time_slot_id)` chỉ áp dụng cho các booking đang "chiếm chỗ"
  (`PENDING`/`AWAITING_CONFIRMATION`/`CONFIRMED`/`COMPLETED`) — xem
  `src/app/models/booking.py` và
  `src/app/services/booking_service.py::create_booking`/`reschedule_booking`. Đã
  kiểm thử: 2 lượt đặt trùng khung giờ, lượt thứ 2 luôn bị từ chối với thông báo
  nghiệp vụ rõ ràng.
- **State machine Booking:** khai báo tường minh bảng chuyển trạng thái hợp lệ
  (`ALLOWED_TRANSITIONS` trong `booking_service.py`), từ chối mọi transition không
  hợp lệ (VD: `COMPLETED → PENDING`), bao gồm cả bước trung gian
  `AWAITING_CONFIRMATION` (khách nộp minh chứng, chờ nhân viên đối chiếu).
- **Quy trình duyệt Cơ sở sân:** `Facility` tách khỏi `Field`, có `status`
  (PENDING/APPROVED/REJECTED); chỉ Quản trị viên mới chuyển được sang `APPROVED`;
  các Sân thuộc cơ sở chưa duyệt bị lọc khỏi kết quả tìm kiếm công khai.
- **Phân quyền theo Cơ sở sân:** mỗi Nhân viên gắn với đúng một Cơ sở sân
  (`User.facility_id`), chỉ thấy/thao tác trên dữ liệu của cơ sở đó ở các trang
  vận hành (G4).
- **Validate client + server:** các trang NiceGUI kiểm tra input cơ bản (bắt buộc
  nhập, số dương...) trước khi gọi service; toàn bộ ràng buộc nghiệp vụ quan trọng
  (giá > 0, giờ bắt đầu < giờ kết thúc, không đặt ngày quá khứ, không trùng lịch,
  đổi lịch/hủy phải đúng chính sách theo giờ...) vẫn được service/DB kiểm tra lại
  độc lập với UI.
