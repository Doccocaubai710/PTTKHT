# Hệ thống đặt sân thể thao (PTTKHT)

Đồ án môn Phân tích thiết kế hệ thống — nền tảng web đặt sân thể thao (bóng đá mini,
cầu lông, tennis) cho phép Khách hàng tìm & đặt sân online, Chủ sân quản lý khung
giờ/giá, Nhân viên vận hành tại quầy.

> Đây là bản baseline phục vụ demo luồng nghiệp vụ + là cơ sở để vẽ tay các sơ đồ
> UML (xem thư mục `docs/`). Cổng thanh toán, SMS/email đều được **mock** — không
> gọi dịch vụ bên ngoài thật.

## Tech stack

- **Ngôn ngữ:** Python 3.11
- **Backend / UI:** [NiceGUI](https://nicegui.io) (xây trên FastAPI + Starlette) —
  giao diện web render từ Python, nút bấm gọi thẳng hàm Python qua WebSocket, không
  cần viết riêng frontend JavaScript/React.
- **ORM / Data access:** SQLAlchemy 2.x
- **Database:** SQLite (file, không cần cài DB server)
- **Auth:** JWT (PyJWT) phát hành khi đăng nhập, lưu trong session trình duyệt
  (`app.storage.user`), kiểm tra lại ở mỗi trang được bảo vệ theo role
  (`CUSTOMER` / `FIELD_OWNER` / `STAFF`)
- **Mật khẩu:** bcrypt

> Lưu ý: ban đầu đồ án dự kiến Node.js/Express/React, nhưng do máy phát triển
> không có sẵn Node.js và theo yêu cầu của người dùng, toàn bộ hệ thống được
> chuyển sang 100% Python (NiceGUI) để có thể cài đặt & chạy nhanh trong 1 tuần
> mà vẫn giữ đúng kiến trúc 3 lớp (Presentation – Business Logic – Data Access)
> và đầy đủ yêu cầu kỹ thuật (chống trùng lịch, state machine, JWT, validate).

## Cấu trúc thư mục

```
/src/app
  /core         Cấu hình, kết nối DB (SQLAlchemy), bảo mật (JWT/bcrypt)
  /models       Entity: User, Field, FieldTimeSlot, Booking, Review, enums
  /repositories Data Access layer (CRUD thuần, không chứa business rule)
  /services     Business Logic layer (auth, booking, field, review)
  /pages        Presentation layer: các trang NiceGUI (@ui.page) cho 8 UC
  main.py       Entry point, đăng ký route + job tự động hết hạn booking
  seed.py       Script tạo dữ liệu mẫu
/docs
  /use-cases        Đặc tả chi tiết 8 Use Case (UC001.md ... UC008.md)
  /diagram-drafts   Draft text cho package/use-case/class/sequence/state diagram
  architecture.md   Kiến trúc hệ thống + design pattern đã áp dụng
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
- 3 sân: bóng đá mini (Cầu Giấy), cầu lông (Thanh Xuân), tennis (Đống Đa), mỗi sân
  5 khung giờ (sáng sớm + tối)
- 3 tài khoản demo (mật khẩu đều là `123456`):

| Vai trò | Số điện thoại | Mật khẩu |
|---|---|---|
| Khách hàng | 0900000002 | 123456 |
| Chủ sân | 0900000001 | 123456 |
| Nhân viên | 0900000003 | 123456 |

Chạy lại `python -m app.seed` khi đã có dữ liệu sẽ tự bỏ qua (không tạo trùng).

## Chạy ứng dụng

```bash
cd src
python -m app.main
```

Mở trình duyệt tại **http://localhost:8090/login**.

Ứng dụng cũng chạy một job nền kiểm tra mỗi 30 giây để tự động chuyển các lượt đặt
sân `PENDING` quá 10 phút chưa thanh toán sang `EXPIRED` (theo state machine ở
`docs/diagram-drafts/state-machine-booking.md`).

## Luồng demo nhanh theo từng UC

1. Đăng nhập bằng tài khoản Khách hàng → **Tìm sân** → chọn sân → chọn ngày/khung
   giờ trống → **Đặt khung giờ này** (UC002, UC003).
2. Vào **Đặt sân của tôi** → **Thanh toán cọc** (mock) để chuyển `PENDING` →
   `CONFIRMED` (UC004); hoặc **Hủy** để xem chính sách hoàn cọc (UC005).
3. Đăng xuất, đăng nhập tài khoản Chủ sân → **Sân của tôi** để thêm khung giờ/sửa
   giá (UC006), hoặc **Đăng ký sân mới**; xem **Doanh thu** để xem báo cáo.
4. Đăng xuất, đăng nhập tài khoản Nhân viên → **Đặt hộ khách** nhập tên/SĐT khách
   walk-in rồi đặt khung giờ (UC007); sang **Đặt sân hôm nay** để xác nhận thanh
   toán tiền mặt hoặc check-in.
5. Sau khi nhân viên bấm **Check-in / hoàn tất** (booking chuyển `COMPLETED`),
   đăng nhập lại tài khoản khách hàng tương ứng để **Đánh giá sân** (UC008).

## Yêu cầu kỹ thuật trọng tâm đã triển khai

- **Chống trùng lịch:** partial unique index trên `(field_id, booking_date,
  time_slot_id)` chỉ áp dụng cho các booking đang "chiếm chỗ"
  (`PENDING`/`CONFIRMED`/`COMPLETED`) — xem `src/app/models/booking.py` và
  `src/app/services/booking_service.py::create_booking`. Đã kiểm thử: 2 lượt đặt
  trùng khung giờ, lượt thứ 2 luôn bị từ chối với thông báo nghiệp vụ rõ ràng.
- **State machine Booking:** khai báo tường minh bảng chuyển trạng thái hợp lệ
  (`ALLOWED_TRANSITIONS` trong `booking_service.py`), từ chối mọi transition không
  hợp lệ (VD: `COMPLETED → PENDING`).
- **Validate client + server:** các trang NiceGUI kiểm tra input cơ bản (bắt buộc
  nhập, số dương...) trước khi gọi service; toàn bộ ràng buộc nghiệp vụ quan trọng
  (giá > 0, giờ bắt đầu < giờ kết thúc, không đặt ngày quá khứ, không trùng lịch...)
  vẫn được service/DB kiểm tra lại độc lập với UI.
