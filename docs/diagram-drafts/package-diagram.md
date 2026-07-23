# Draft — Biểu đồ gói (Package Diagram)

> Ghi chú: file này chỉ mô tả bằng text để tự vẽ tay. Cấu trúc thư mục thật nằm ở
> `src/app/*`, ánh xạ 1-1 với các package liệt kê dưới đây.

## Danh sách package

| Package | Vai trò (lớp kiến trúc) | Thư mục tương ứng |
|---|---|---|
| `pages` | Presentation Layer | `src/app/pages` |
| `services` | Business Logic Layer | `src/app/services` |
| `repositories` | Data Access Layer | `src/app/repositories` |
| `models` | Domain Model / Entity | `src/app/models` |
| `core` | Cross-cutting (hạ tầng dùng chung) | `src/app/core` |

## Quan hệ phụ thuộc (dependency)

```
pages  ---> services   (Presentation gọi Business Logic)
pages  ---> models     (chỉ để tham chiếu enum hiển thị, VD SportType, BookingStatus)
pages  ---> core.guards/security gián tiếp qua "pages.guards" (kiểm tra JWT trong phiên)

services ---> repositories  (Business Logic gọi Data Access để đọc/ghi)
services ---> models         (Business Logic thao tác trực tiếp trên entity)
services ---> core.database  (mở session/transaction)
services ---> core.config    (đọc hằng số nghiệp vụ: DEPOSIT_RATIO, BOOKING_HOLD_MINUTES...)
services ---> core.security  (auth_service dùng để hash/verify password, tạo JWT)

repositories ---> models        (repository trả về/nhận vào entity)
repositories ---> core.database (dùng Session do core.database cung cấp)

models ---> core.database  (Base declarative để khai báo bảng)
```

## Vì sao có các phụ thuộc này

- **`pages` phụ thuộc `services`, không phụ thuộc `repositories`:** Presentation layer
  không được phép "nhảy cóc" thẳng xuống Data Access — mọi nghiệp vụ (validate, tính
  tiền cọc, kiểm tra state machine...) phải đi qua `services` để đảm bảo tính nhất
  quán, tránh trùng lặp logic giữa các trang.
- **`services` phụ thuộc `repositories`, không phụ thuộc `pages`:** đảm bảo tầng
  Business Logic độc lập với giao diện — có thể viết unit test cho `services` mà
  không cần khởi động NiceGUI, và về sau có thể thay UI (VD viết thêm REST API)
  mà không phải sửa `services`.
- **`repositories` phụ thuộc `models`, không phụ thuộc `services`:** tránh phụ
  thuộc vòng (circular dependency); repository chỉ biết "đọc/ghi entity nào", không
  biết gì về nghiệp vụ nào đang gọi nó.
- **`core` là tầng thấp nhất**, không phụ thuộc ngược lên `models`/`repositories`/
  `services`/`pages` — mọi package khác đều có thể phụ thuộc `core`, nhưng `core`
  không phụ thuộc lại bất kỳ package nghiệp vụ nào (tránh phụ thuộc vòng, dễ tái sử
  dụng `core` cho phần mở rộng khác nếu có).

## Package bên ngoài (thư viện)

| Package ngoài | Được dùng bởi | Mục đích |
|---|---|---|
| `nicegui` | `pages`, `app/main.py` | Render UI, xử lý route/điều hướng, WebSocket |
| `sqlalchemy` | `core.database`, `models`, `repositories` | ORM, quản lý Session/transaction |
| `pyjwt` | `core.security` | Tạo/giải mã JWT |
| `bcrypt` | `core.security` | Băm mật khẩu |
