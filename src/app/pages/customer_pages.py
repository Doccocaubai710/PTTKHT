"""Presentation layer cho UC05 (tìm sân), UC06 (xem chi tiết), UC07 (lịch trống),
UC08 (đặt sân), UC09 (đặt cọc), UC10 (hủy), UC11 (đổi lịch), UC12 (lịch sử),
UC22 (đánh giá) và gửi khiếu nại (UC27, phía người gửi)."""
from datetime import date

from nicegui import ui

from app.models.enums import BookingStatus, SportType, UserRole
from app.pages.common import (
    COMPLAINT_STATUS_COLORS,
    COMPLAINT_STATUS_LABELS,
    SPORT_TYPE_LABELS,
    STATUS_COLORS,
    STATUS_LABELS,
    header,
)
from app.pages.guards import require_role
from app.services.booking_service import BookingError, BookingService
from app.services.complaint_service import ComplaintError, ComplaintService
from app.services.field_service import FieldService
from app.services.review_service import ReviewError, ReviewService

field_service = FieldService()
booking_service = BookingService()
review_service = ReviewService()
complaint_service = ComplaintService()

NAV_LINKS = [
    ("Tìm sân", "/search"),
    ("Đặt sân của tôi", "/my-bookings"),
    ("Khiếu nại của tôi", "/my-complaints"),
]


@ui.page("/search")
def search_page():
    user = require_role(UserRole.CUSTOMER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Tìm sân thể thao").classes("text-2xl font-bold mt-4 mx-4")

    with ui.row().classes("mx-4 gap-4"):
        area_input = ui.input("Khu vực (VD: Cầu Giấy)").classes("w-64")
        sport_select = ui.select(
            {"": "Tất cả loại sân", **{s.value: SPORT_TYPE_LABELS[s.value] for s in SportType}},
            value="",
            label="Loại sân",
        ).classes("w-64")

    results_container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def do_search():
        results_container.clear()
        sport_type = SportType(sport_select.value) if sport_select.value else None
        fields = field_service.search_fields(area=area_input.value or None, sport_type=sport_type)
        if not fields:
            with results_container:
                ui.label("Không tìm thấy sân phù hợp.")
            return
        with results_container:
            for f in fields:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f"{f.name} ({f.facility_name})").classes("text-lg font-bold")
                            ui.label(f"{SPORT_TYPE_LABELS[f.sport_type.value]} • {f.area} • {f.address}")
                            if f.description:
                                ui.label(f.description).classes("text-sm text-gray-500")
                        ui.button(
                            "Xem khung giờ & đặt sân", on_click=lambda fid=f.field_id: ui.navigate.to(f"/field/{fid}")
                        )

    ui.button("Tìm kiếm", on_click=do_search).classes("mx-4")
    do_search()


@ui.page("/field/{field_id}")
def field_detail_page(field_id: int):
    user = require_role(UserRole.CUSTOMER)
    if not user:
        return

    field = field_service.get_field_summary(field_id)
    if not field:
        ui.label("Không tìm thấy sân.")
        return

    header(user, NAV_LINKS)
    ui.label(f"{field.name} ({field.facility_name})").classes("text-2xl font-bold mt-4 mx-4")
    ui.label(f"{SPORT_TYPE_LABELS[field.sport_type.value]} • {field.area} • {field.address}").classes("mx-4")

    with ui.row().classes("mx-4 mt-4 items-center gap-4"):
        date_input = ui.date(value=date.today().isoformat()).props("minimal")

    slots_container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def book_slot(slot_id: int):
        try:
            booking = booking_service.create_booking(
                field_id=field.field_id,
                time_slot_id=slot_id,
                booking_date=date.fromisoformat(date_input.value),
                customer_id=user.user_id,
                created_by_id=user.user_id,
            )
            ui.notify(
                f"Đặt sân thành công (mã #{booking.id}), vui lòng thanh toán cọc trong ít phút.",
                type="positive",
            )
            ui.navigate.to("/my-bookings")
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def refresh_slots():
        slots_container.clear()
        on_date = date.fromisoformat(date_input.value)
        availability = field_service.get_availability(field.field_id, on_date)
        if not availability:
            with slots_container:
                ui.label("Sân này chưa có khung giờ nào được thiết lập.")
            return
        with slots_container:
            for slot in availability:
                with ui.row().classes("items-center gap-4 border p-2 rounded w-full justify-between"):
                    ui.label(f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}")
                    ui.label(f"{slot.price:,.0f} đ")
                    if slot.is_booked:
                        ui.badge("Đã đặt").props("color=grey")
                    else:
                        ui.button("Đặt khung giờ này", on_click=lambda sid=slot.slot_id: book_slot(sid))

    date_input.on_value_change(lambda e: refresh_slots())
    refresh_slots()


@ui.page("/my-bookings")
def my_bookings_page():
    user = require_role(UserRole.CUSTOMER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Đặt sân của tôi").classes("text-2xl font-bold mt-4 mx-4")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def submit_proof_dialog(booking_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nộp minh chứng chuyển khoản").classes("text-lg font-bold")
            ui.label("(Demo) Chuyển khoản theo mã QR rồi nhập mã giao dịch/nội dung chuyển khoản bên dưới.")
            proof = ui.input("Mã giao dịch / nội dung chuyển khoản").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    booking_service.submit_payment_proof(booking_id, user.user_id, proof.value)
                    ui.notify("Đã gửi minh chứng, chờ nhân viên xác nhận.", type="positive")
                    dialog.close()
                    refresh()
                except BookingError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Gửi minh chứng", on_click=submit)
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def cancel(booking_id: int):
        try:
            result = booking_service.cancel_booking(booking_id, reason="Khách hàng tự hủy")
            ui.notify(f"Đã hủy đặt sân. Số tiền hoàn lại: {result.refund_amount:,.0f} đ", type="warning")
            refresh()
        except BookingError as e:
            ui.notify(str(e), type="negative")

    def reschedule_dialog(booking_id: int, field_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Đổi lịch đặt sân").classes("text-lg font-bold")
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
                                ui.notify("Đổi lịch thành công.", type="positive")
                                dialog.close()
                                refresh()
                            except BookingError as e:
                                error_label.text = str(e)

                        ui.button(label, on_click=do_reschedule).classes("w-full")

            new_date.on_value_change(lambda e: refresh_slots())
            refresh_slots()
            ui.button("Đóng", on_click=dialog.close).classes("mt-2")
        dialog.open()

    def complaint_dialog(booking_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Gửi khiếu nại").classes("text-lg font-bold")
            subject = ui.input("Tiêu đề").classes("w-full")
            description = ui.textarea("Nội dung khiếu nại").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    complaint_service.submit_complaint(
                        created_by_id=user.user_id,
                        subject=subject.value,
                        description=description.value,
                        booking_id=booking_id,
                    )
                    ui.notify("Đã gửi khiếu nại tới quản trị viên.", type="positive")
                    dialog.close()
                except ComplaintError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Gửi khiếu nại", on_click=submit)
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def open_review_dialog(booking_id: int):
        with ui.dialog() as dialog, ui.card():
            ui.label("Đánh giá sân").classes("text-lg font-bold")
            rating = ui.number("Số sao (1-5)", value=5, min=1, max=5)
            comment = ui.textarea("Nhận xét (tùy chọn)")

            def submit():
                try:
                    review_service.submit_review(
                        booking_id=booking_id,
                        customer_id=user.user_id,
                        rating=int(rating.value),
                        comment=comment.value or None,
                    )
                    ui.notify("Cảm ơn bạn đã đánh giá!", type="positive")
                    dialog.close()
                    refresh()
                except ReviewError as e:
                    ui.notify(str(e), type="negative")

            with ui.row():
                ui.button("Gửi đánh giá", on_click=submit)
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def refresh():
        container.clear()
        bookings = booking_service.list_customer_bookings(user.user_id)
        if not bookings:
            with container:
                ui.label("Bạn chưa có đặt sân nào.")
            return
        with container:
            for b in bookings:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f"Mã đặt sân #{b.id} - Sân #{b.field_id} - Ngày {b.booking_date}")
                            ui.label(f"Tổng tiền: {b.total_price:,.0f} đ | Cọc: {b.deposit_amount:,.0f} đ")
                            if b.status == BookingStatus.PENDING:
                                ui.label(f"Giữ chỗ đến: {b.hold_expires_at.strftime('%H:%M:%S %d/%m/%Y')}").classes(
                                    "text-sm text-orange-600"
                                )
                                if b.payment_rejected_reason:
                                    ui.label(f"Minh chứng bị từ chối: {b.payment_rejected_reason}").classes(
                                        "text-sm text-red-600"
                                    )
                            if b.status == BookingStatus.AWAITING_CONFIRMATION:
                                ui.label("Đang chờ nhân viên đối chiếu minh chứng chuyển khoản.").classes(
                                    "text-sm text-purple-600"
                                )
                            if b.refund_amount is not None:
                                ui.label(f"Đã hoàn: {b.refund_amount:,.0f} đ").classes("text-sm")
                        with ui.column().classes("items-end gap-1"):
                            ui.badge(STATUS_LABELS[b.status.value]).props(f"color={STATUS_COLORS[b.status.value]}")
                            with ui.row().classes("gap-1"):
                                if b.status == BookingStatus.PENDING:
                                    ui.button("Nộp minh chứng", on_click=lambda bid=b.id: submit_proof_dialog(bid))
                                    ui.button("Hủy", on_click=lambda bid=b.id: cancel(bid)).props("color=negative")
                                elif b.status == BookingStatus.AWAITING_CONFIRMATION:
                                    ui.button("Hủy", on_click=lambda bid=b.id: cancel(bid)).props("color=negative")
                                elif b.status == BookingStatus.CONFIRMED:
                                    ui.button(
                                        "Đổi lịch",
                                        on_click=lambda bid=b.id, fid=b.field_id: reschedule_dialog(bid, fid),
                                    )
                                    ui.button("Hủy", on_click=lambda bid=b.id: cancel(bid)).props("color=negative")
                                elif b.status == BookingStatus.COMPLETED:
                                    ui.button("Đánh giá sân", on_click=lambda bid=b.id: open_review_dialog(bid))
                                if b.status in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED):
                                    ui.button(
                                        "Khiếu nại", on_click=lambda bid=b.id: complaint_dialog(bid)
                                    ).props("flat")

    refresh()


@ui.page("/my-complaints")
def my_complaints_page():
    user = require_role(UserRole.CUSTOMER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Khiếu nại của tôi").classes("text-2xl font-bold mt-4 mx-4")

    complaints = complaint_service.list_my_complaints(user.user_id)
    with ui.column().classes("mx-4 mt-4 w-full gap-2"):
        if not complaints:
            ui.label("Bạn chưa gửi khiếu nại nào.")
        for c in complaints:
            with ui.card().classes("w-full"):
                with ui.row().classes("justify-between items-center w-full"):
                    with ui.column():
                        ui.label(c.subject).classes("font-bold")
                        ui.label(c.description).classes("text-sm")
                        if c.resolution_note:
                            ui.label(f"Phản hồi: {c.resolution_note}").classes("text-sm text-blue-600")
                    ui.badge(COMPLAINT_STATUS_LABELS[c.status.value]).props(
                        f"color={COMPLAINT_STATUS_COLORS[c.status.value]}"
                    )
