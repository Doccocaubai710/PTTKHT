"""Entry point ứng dụng: khởi tạo DB, đăng ký các trang NiceGUI (presentation layer),
và chạy một background job định kỳ để tự động hết hạn các booking PENDING quá lâu.

Chạy: python -m app.main  (từ thư mục src/, với conda env sportbook đã cài requirements)
"""
import asyncio

from nicegui import app, ui

from app.core.config import STORAGE_SECRET
from app.core.database import init_db
from app.pages.guards import get_current_user, home_path_for_role
from app.services.booking_service import BookingService

# Import các trang để NiceGUI đăng ký route (@ui.page) khi module được load.
from app.pages import auth_pages, customer_pages, owner_pages, staff_pages  # noqa: F401

booking_service = BookingService()


@ui.page("/")
def index_page():
    user = get_current_user()
    if user:
        ui.navigate.to(home_path_for_role(user.role))
    else:
        ui.navigate.to("/login")


async def _expire_loop():
    # Kiểm tra mỗi 30s xem có booking PENDING nào quá 10 phút giữ chỗ chưa thanh toán không.
    while True:
        await asyncio.sleep(30.0)
        count = booking_service.expire_overdue_bookings()
        if count:
            print(f"[scheduler] Đã chuyển {count} đặt sân PENDING quá hạn sang EXPIRED.")


def _on_startup():
    init_db()
    asyncio.create_task(_expire_loop())


app.on_startup(_on_startup)

ui.run(title="Hệ thống đặt sân thể thao", storage_secret=STORAGE_SECRET, port=8090, reload=False)
