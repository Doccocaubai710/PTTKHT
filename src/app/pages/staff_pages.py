"""Presentation layer cho UC18 (xác nhận thanh toán), UC19 (check-in khách),
UC20 (đặt sân trực tiếp cho khách vãng lai) và UC21 (xử lý yêu cầu đổi/hủy tại chỗ).
Toàn bộ trang được giới hạn theo Cơ sở sân (facility_id) mà nhân viên đang thuộc về."""
from datetime import date

from nicegui import ui

from app.core.database import get_session
from app.core.security import hash_password
from app.models.enums import BookingStatus, UserRole
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

NAV_LINKS = [
    ("Đặt hộ khách", "/staff"),
    ("Đặt sân hôm nay", "/staff/today"),
]


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


def _staff_facility_id(user) -> int | None:
    with get_session() as session:
        staff = user_repo.get_by_id(session, user.user_id)
        return staff.facility_id if staff else None


@ui.page("/staff")
def staff_page():
    user = require_role(UserRole.STAFF)
    if not user:
        return

    facility_id = _staff_facility_id(user)
    header(user, NAV_LINKS)
    ui.label("Đặt sân hộ khách walk-in").classes("text-2xl font-bold mt-4 mx-4")

    if not facility_id:
        ui.label(
            "Tài khoản của bạn chưa được gán vào cơ sở sân nào. Vui lòng liên hệ Chủ sân."
        ).classes("mx-4 text-red-600")
        return

    with ui.row().classes("mx-4 gap-4"):
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
            ui.notify(
                f"Đã tạo đặt sân #{booking.id} cho khách. Nhớ xác nhận thanh toán ở tab bên.", type="positive"
            )
            refresh_fields()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def refresh_fields():
        fields_container.clear()
        fields = field_service.list_facility_fields(facility_id)
        on_date = date.fromisoformat(date_input.value)
        with fields_container:
            if not fields:
                ui.label("Cơ sở của bạn chưa có sân nào.")
            for f in fields:
                with ui.expansion(f"{f.name} ({SPORT_TYPE_LABELS[f.sport_type.value]})").classes("w-full"):
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

    date_input.on_value_change(lambda e: refresh_fields())
    ui.button("Làm mới", on_click=refresh_fields).classes("mx-4")
    refresh_fields()


@ui.page("/staff/today")
def staff_today_page():
    user = require_role(UserRole.STAFF)
    if not user:
        return

    facility_id = _staff_facility_id(user)
    header(user, NAV_LINKS)
    ui.label("Danh sách đặt sân - vận hành hằng ngày").classes("text-2xl font-bold mt-4 mx-4")
    ui.label(
        "Đối chiếu minh chứng chuyển khoản (UC18), xác nhận thu tiền mặt, check-in (UC19) "
        "và xử lý đổi/hủy tại chỗ (UC21)."
    ).classes("mx-4 text-sm text-gray-500")

    if not facility_id:
        ui.label(
            "Tài khoản của bạn chưa được gán vào cơ sở sân nào. Vui lòng liên hệ Chủ sân."
        ).classes("mx-4 text-red-600")
        return

    with ui.row().classes("mx-4 gap-4"):
        date_input = ui.date(value=date.today().isoformat()).classes("w-48")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def confirm_cash(booking_id: int):
        try:
            booking_service.confirm_cash_payment(booking_id, user.user_id)
            ui.notify("Đã xác nhận thanh toán tiền mặt.", type="positive")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def confirm_online(booking_id: int):
        try:
            booking_service.confirm_payment(booking_id, user.user_id)
            ui.notify("Đã xác nhận giao dịch chuyển khoản.", type="positive")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def reject_dialog(booking_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Từ chối minh chứng thanh toán").classes("text-lg font-bold")
            reason = ui.input("Lý do từ chối").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    booking_service.reject_payment(booking_id, user.user_id, reason.value)
                    ui.notify("Đã từ chối, khách cần bổ sung minh chứng khác.", type="warning")
                    dialog.close()
                    refresh()
                except BookingError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Từ chối", on_click=submit).props("color=negative")
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def check_in(booking_id: int):
        try:
            booking_service.check_in_and_complete(booking_id)
            ui.notify("Đã check-in / hoàn tất lượt sử dụng sân.", type="positive")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def cancel_onsite(booking_id: int):
        try:
            result = booking_service.cancel_booking(booking_id, reason="Nhân viên xử lý hủy tại chỗ")
            ui.notify(f"Đã hủy đặt sân. Hoàn cọc: {result.refund_amount:,.0f} đ", type="warning")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def reschedule_dialog(booking_id: int, field_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Đổi lịch tại chỗ cho khách").classes("text-lg font-bold")
            new_date = ui.date(value=date.today().isoformat()).props("minimal")
            slots_col = ui.column().classes("gap-1 mt-2")
            error_label = ui.label("").classes("text-red-500")

            def refresh_slots():
                slots_col.clear()
                on_date = date.fromisoformat(new_date.value)
                availability = field_service.get_availability(field_id, on_date)
                with slots_col:
                    for slot in availability:
                        if slot.is_booked:
                            continue
                        label = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')} ({slot.price:,.0f} đ)"

                        def do_reschedule(sid=slot.slot_id):
                            try:
                                booking_service.reschedule_booking(
                                    booking_id, field_id, sid, date.fromisoformat(new_date.value)
                                )
                                ui.notify("Đã đổi lịch cho khách.", type="positive")
                                dialog.close()
                                refresh()
                            except BookingError as e:
                                error_label.text = str(e)

                        ui.button(label, on_click=do_reschedule).classes("w-full")

            new_date.on_value_change(lambda e: refresh_slots())
            refresh_slots()
            ui.button("Đóng", on_click=dialog.close).classes("mt-2")
        dialog.open()

    def refresh():
        container.clear()
        on_date = date.fromisoformat(date_input.value)
        bookings = booking_service.list_facility_bookings(facility_id, on_date)
        with container:
            if not bookings:
                ui.label("Không có đặt sân nào cần xử lý trong ngày này.")
            for b in bookings:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f"#{b.id} - Sân #{b.field_id} - Ngày {b.booking_date}")
                            if b.status == BookingStatus.AWAITING_CONFIRMATION and b.payment_proof_ref:
                                ui.label(f"Minh chứng: {b.payment_proof_ref}").classes("text-sm text-purple-600")
                        ui.badge(STATUS_LABELS[b.status.value]).props(f"color={STATUS_COLORS[b.status.value]}")
                        with ui.row().classes("gap-1"):
                            if b.status == BookingStatus.PENDING:
                                ui.button("Xác nhận tiền mặt", on_click=lambda bid=b.id: confirm_cash(bid))
                            elif b.status == BookingStatus.AWAITING_CONFIRMATION:
                                ui.button("Xác nhận khớp", on_click=lambda bid=b.id: confirm_online(bid))
                                ui.button("Từ chối", on_click=lambda bid=b.id: reject_dialog(bid)).props(
                                    "color=negative"
                                )
                            elif b.status == BookingStatus.CONFIRMED:
                                ui.button("Check-in / hoàn tất", on_click=lambda bid=b.id: check_in(bid))
                                ui.button(
                                    "Đổi lịch",
                                    on_click=lambda bid=b.id, fid=b.field_id: reschedule_dialog(bid, fid),
                                ).props("flat")
                            if b.status in (
                                BookingStatus.PENDING,
                                BookingStatus.AWAITING_CONFIRMATION,
                                BookingStatus.CONFIRMED,
                            ):
                                ui.button("Hủy tại chỗ", on_click=lambda bid=b.id: cancel_onsite(bid)).props(
                                    "flat color=negative"
                                )

    date_input.on_value_change(lambda e: refresh())
    refresh()
