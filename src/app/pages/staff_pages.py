"""Presentation layer cho UC007 - Nhân viên đặt hộ khách walk-in tại quầy
(bao gồm check-in và xác nhận thanh toán tiền mặt)."""
from datetime import date

from nicegui import ui

from app.core.database import get_session
from app.core.security import hash_password
from app.models.enums import BookingStatus, SportType, UserRole
from app.models.user import User
from app.pages.common import SPORT_TYPE_LABELS, STATUS_COLORS, STATUS_LABELS, header
from app.pages.guards import require_role
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingError, BookingService
from app.services.field_service import FieldService

field_service = FieldService()
booking_service = BookingService()
user_repo = UserRepository()

WALKIN_DEFAULT_PASSWORD = "walkin123"


def _get_or_create_customer(full_name: str, phone: str) -> int:
    """Tìm khách theo SĐT; nếu chưa có tài khoản (khách vãng lai) thì tạo nhanh
    một tài khoản CUSTOMER với mật khẩu mặc định để có thể tra cứu lịch sử sau này."""
    with get_session() as session:
        existing = user_repo.get_by_phone(session, phone)
        if existing:
            return existing.id
        new_user = User(
            full_name=full_name,
            phone=phone,
            password_hash=hash_password(WALKIN_DEFAULT_PASSWORD),
            role=UserRole.CUSTOMER,
        )
        user_repo.add(session, new_user)
        return new_user.id


@ui.page("/staff")
def staff_page():
    user = require_role(UserRole.STAFF)
    if not user:
        return

    header(user, [("Đặt hộ khách", "/staff"), ("Đặt sân hôm nay", "/staff/today")])
    ui.label("Đặt sân hộ khách walk-in").classes("text-2xl font-bold mt-4 mx-4")

    with ui.row().classes("mx-4 gap-4"):
        area_input = ui.input("Khu vực").classes("w-48")
        sport_select = ui.select(
            {"": "Tất cả loại sân", **{s.value: SPORT_TYPE_LABELS[s.value] for s in SportType}},
            value="",
            label="Loại sân",
        ).classes("w-48")
        date_input = ui.date(value=date.today().isoformat()).classes("w-48")

    fields_container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    with ui.card().classes("mx-4 mt-4 w-96"):
        ui.label("Thông tin khách hàng").classes("font-bold")
        customer_name = ui.input("Họ tên khách").classes("w-full")
        customer_phone = ui.input("Số điện thoại khách").classes("w-full")
        ui.label("Nếu số điện thoại chưa có tài khoản, hệ thống sẽ tự tạo tài khoản khách mới.").classes(
            "text-xs text-gray-500"
        )

    def book_for_customer(field_id: int, slot_id: int):
        if not customer_name.value or not customer_phone.value:
            ui.notify("Vui lòng nhập tên và số điện thoại khách trước khi đặt.", type="warning")
            return
        try:
            customer_id = _get_or_create_customer(customer_name.value, customer_phone.value)
            booking = booking_service.create_booking(
                field_id=field_id,
                time_slot_id=slot_id,
                booking_date=date.fromisoformat(date_input.value),
                customer_id=customer_id,
                created_by_id=user.user_id,
            )
            ui.notify(f"Đã tạo đặt sân #{booking.id} cho khách. Nhớ xác nhận thanh toán ở tab bên.", type="positive")
            refresh_fields()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def refresh_fields():
        fields_container.clear()
        sport_type = SportType(sport_select.value) if sport_select.value else None
        fields = field_service.search_fields(area=area_input.value or None, sport_type=sport_type)
        on_date = date.fromisoformat(date_input.value)
        with fields_container:
            for f in fields:
                with ui.expansion(f"{f.name} - {f.area} ({SPORT_TYPE_LABELS[f.sport_type.value]})").classes("w-full"):
                    availability = field_service.get_availability(f.id, on_date)
                    for slot in availability:
                        with ui.row().classes("items-center gap-4"):
                            ui.label(f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}")
                            ui.label(f"{slot.price:,.0f} đ")
                            if slot.is_booked:
                                ui.badge("Đã đặt")
                            else:
                                ui.button(
                                    "Đặt cho khách",
                                    on_click=lambda fid=f.id, sid=slot.slot_id: book_for_customer(fid, sid),
                                )

    ui.button("Tìm sân", on_click=refresh_fields).classes("mx-4")
    refresh_fields()


@ui.page("/staff/today")
def staff_today_page():
    user = require_role(UserRole.STAFF)
    if not user:
        return

    header(user, [("Đặt hộ khách", "/staff"), ("Đặt sân hôm nay", "/staff/today")])
    ui.label("Danh sách đặt sân - check-in & xác nhận thanh toán").classes("text-2xl font-bold mt-4 mx-4")
    ui.label(
        "Nhân viên xác nhận thanh toán tiền mặt (chuyển PENDING -> CONFIRMED) "
        "và check-in sau khi khách chơi xong (chuyển CONFIRMED -> COMPLETED)."
    ).classes("mx-4 text-sm text-gray-500")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def confirm_cash(booking_id: int):
        try:
            booking_service.confirm_cash_payment(booking_id)
            ui.notify("Đã xác nhận thanh toán tiền mặt.", type="positive")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def check_in(booking_id: int):
        try:
            booking_service.check_in_and_complete(booking_id)
            ui.notify("Đã check-in / hoàn tất lượt sử dụng sân.", type="positive")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def refresh():
        container.clear()
        today = date.today()
        relevant = [
            b
            for b in _list_all_bookings_today(today)
            if b.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)
        ]
        with container:
            if not relevant:
                ui.label("Không có đặt sân nào cần xử lý hôm nay.")
            for b in relevant:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        ui.label(f"#{b.id} - Sân #{b.field_id} - Ngày {b.booking_date}")
                        ui.badge(STATUS_LABELS[b.status.value]).props(f"color={STATUS_COLORS[b.status.value]}")
                        with ui.row():
                            if b.status == BookingStatus.PENDING:
                                ui.button("Xác nhận đã thu tiền mặt", on_click=lambda bid=b.id: confirm_cash(bid))
                            elif b.status == BookingStatus.CONFIRMED:
                                ui.button("Check-in / hoàn tất", on_click=lambda bid=b.id: check_in(bid))

    refresh()


def _list_all_bookings_today(on_date: date):
    """Demo đơn giản: lấy toàn bộ booking trong ngày trên tất cả các sân bằng cách
    duyệt qua repository trực tiếp (đủ dùng cho quy mô dữ liệu demo của đồ án)."""
    from sqlalchemy import select

    from app.core.database import get_session
    from app.models.booking import Booking

    with get_session() as session:
        stmt = select(Booking).where(Booking.booking_date == on_date)
        bookings = list(session.execute(stmt).scalars().all())
        session.expunge_all()
        return bookings
