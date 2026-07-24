"""Presentation layer cho UC13 (đăng ký/cập nhật cơ sở sân), UC14 (quản lý sân & khung giờ),
UC15 (thiết lập giá), UC16 (quản lý tài khoản nhân viên), UC17 (báo cáo doanh thu)
và UC23 (chủ sân phản hồi đánh giá)."""
from datetime import time

from nicegui import ui

from app.models.enums import SportType, UserRole
from app.pages.common import FACILITY_STATUS_COLORS, FACILITY_STATUS_LABELS, SPORT_TYPE_LABELS, header
from app.pages.guards import require_role
from app.services.booking_service import BookingService
from app.services.facility_service import FacilityError, FacilityService
from app.services.field_service import FieldError, FieldService
from app.services.review_service import ReviewError, ReviewService
from app.services.staff_service import StaffError, StaffService

field_service = FieldService()
booking_service = BookingService()
facility_service = FacilityService()
staff_service = StaffService()
review_service = ReviewService()

NAV_LINKS = [
    ("Cơ sở & sân của tôi", "/owner"),
    ("Nhân viên", "/owner/staff"),
    ("Doanh thu", "/owner/revenue"),
    ("Đánh giá", "/owner/reviews"),
]


@ui.page("/owner")
def owner_dashboard_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Cơ sở & sân của tôi").classes("text-2xl font-bold mt-4 mx-4")

    facilities_container = ui.column().classes("mx-4 mt-4 w-full gap-4")

    def refresh():
        facilities_container.clear()
        facilities = facility_service.list_owner_facilities(user.user_id)
        with facilities_container:
            if not facilities:
                ui.label("Bạn chưa đăng ký cơ sở sân nào.")
            for facility in facilities:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f"{facility.name}").classes("text-lg font-bold")
                            ui.label(f"{facility.area} • {facility.address}")
                        ui.badge(FACILITY_STATUS_LABELS[facility.status.value]).props(
                            f"color={FACILITY_STATUS_COLORS[facility.status.value]}"
                        )
                    if facility.status.value == "REJECTED" and facility.reject_reason:
                        ui.label(f"Lý do từ chối: {facility.reject_reason}").classes("text-red-600 text-sm")
                        ui.button(
                            "Chỉnh sửa & gửi lại",
                            on_click=lambda fac=facility: edit_facility_dialog(fac, refresh),
                        ).props("size=sm")

                    if facility.status.value != "APPROVED":
                        ui.label(
                            "Cơ sở sân đang chờ Quản trị viên duyệt, chưa hiển thị công khai cho khách hàng."
                        ).classes("text-sm text-orange-600")
                        continue

                    fields = field_service.list_facility_fields(facility.id)
                    for f in fields:
                        with ui.card().classes("w-full bg-gray-50"):
                            ui.label(f"{f.name} ({SPORT_TYPE_LABELS[f.sport_type.value]})").classes("font-bold")
                            slots = field_service.list_time_slots(f.id)
                            with ui.column().classes("gap-1 mt-2"):
                                for s in slots:
                                    with ui.row().classes("items-center gap-4"):
                                        ui.label(
                                            f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                                        ).classes("w-32")
                                        price_input = ui.number(value=s.price, label="Giá (đ)").classes("w-32")
                                        active_switch = ui.switch("Đang mở", value=s.is_active)

                                        def save_price(sid=s.id, price_in=price_input):
                                            try:
                                                field_service.update_time_slot_price(sid, price_in.value)
                                                ui.notify("Đã cập nhật giá.", type="positive")
                                            except FieldError as e:
                                                ui.notify(str(e), type="negative")

                                        def toggle_active(e, sid=s.id):
                                            field_service.set_time_slot_active(sid, e.value)
                                            ui.notify("Đã cập nhật trạng thái khung giờ.", type="positive")

                                        ui.button("Lưu giá", on_click=save_price).props("size=sm")
                                        active_switch.on_value_change(toggle_active)

                            with ui.row().classes("items-center gap-2 mt-3"):
                                start_input = ui.time(value="06:00").classes("w-32")
                                end_input = ui.time(value="07:00").classes("w-32")
                                new_price_input = ui.number(label="Giá (đ)", value=100000).classes("w-32")

                                def add_slot(fid=f.id, start_in=start_input, end_in=end_input, price_in=new_price_input):
                                    try:
                                        sh, sm = map(int, start_in.value.split(":"))
                                        eh, em = map(int, end_in.value.split(":"))
                                        field_service.add_time_slot(
                                            fid, time(sh, sm), time(eh, em), price_in.value
                                        )
                                        ui.notify("Đã thêm khung giờ mới.", type="positive")
                                        refresh()
                                    except FieldError as e:
                                        ui.notify(str(e), type="negative")

                                ui.button("+ Thêm khung giờ", on_click=add_slot)

                    ui.button(
                        "+ Thêm sân mới trong cơ sở này",
                        on_click=lambda fac_id=facility.id: new_field_dialog(fac_id, refresh),
                    ).classes("mt-2")

    ui.button("＋ Đăng ký cơ sở sân mới", on_click=lambda: new_facility_dialog(refresh)).classes("mx-4")
    refresh()


def new_facility_dialog(on_created):
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Đăng ký cơ sở sân mới").classes("text-lg font-bold")
        name = ui.input("Tên cơ sở").classes("w-full")
        area = ui.input("Khu vực").classes("w-full")
        address = ui.input("Địa chỉ").classes("w-full")
        description = ui.textarea("Mô tả (tùy chọn)").classes("w-full")
        policy = ui.textarea("Chính sách hủy/đổi lịch (tùy chọn)").classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def submit():
            try:
                facility_service.register_facility(
                    owner_id=user.user_id,
                    name=name.value,
                    area=area.value,
                    address=address.value,
                    description=description.value or None,
                    cancellation_policy=policy.value or None,
                )
                dialog.close()
                on_created()
                ui.notify("Đã gửi hồ sơ đăng ký, chờ Quản trị viên duyệt.", type="positive")
            except FacilityError as e:
                error_label.text = str(e)

        with ui.row():
            ui.button("Gửi đăng ký", on_click=submit)
            ui.button("Hủy", on_click=dialog.close)
    dialog.open()


def edit_facility_dialog(facility, on_updated):
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Chỉnh sửa cơ sở sân").classes("text-lg font-bold")
        name = ui.input("Tên cơ sở", value=facility.name).classes("w-full")
        area = ui.input("Khu vực", value=facility.area).classes("w-full")
        address = ui.input("Địa chỉ", value=facility.address).classes("w-full")
        description = ui.textarea("Mô tả (tùy chọn)", value=facility.description or "").classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def submit():
            try:
                facility_service.update_facility(
                    facility_id=facility.id,
                    owner_id=user.user_id,
                    name=name.value,
                    area=area.value,
                    address=address.value,
                    description=description.value or None,
                    cancellation_policy=facility.cancellation_policy,
                )
                dialog.close()
                on_updated()
                ui.notify("Đã gửi lại hồ sơ để duyệt.", type="positive")
            except FacilityError as e:
                error_label.text = str(e)

        with ui.row():
            ui.button("Lưu & gửi lại", on_click=submit)
            ui.button("Hủy", on_click=dialog.close)
    dialog.open()


def new_field_dialog(facility_id: int, on_created):
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Thêm sân mới").classes("text-lg font-bold")
        name = ui.input("Tên sân").classes("w-full")
        sport = ui.select(
            {s.value: SPORT_TYPE_LABELS[s.value] for s in SportType}, value=SportType.FOOTBALL.value, label="Loại sân"
        ).classes("w-full")
        description = ui.textarea("Mô tả (tùy chọn)").classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def submit():
            try:
                field_service.create_field(
                    owner_id=user.user_id,
                    facility_id=facility_id,
                    name=name.value,
                    sport_type=SportType(sport.value),
                    description=description.value or None,
                )
                dialog.close()
                on_created()
                ui.notify("Đã thêm sân mới.", type="positive")
            except FieldError as e:
                error_label.text = str(e)

        with ui.row():
            ui.button("Lưu", on_click=submit)
            ui.button("Hủy", on_click=dialog.close)
    dialog.open()


@ui.page("/owner/staff")
def owner_staff_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Quản lý tài khoản nhân viên").classes("text-2xl font-bold mt-4 mx-4")

    facilities = facility_service.list_owner_facilities(user.user_id)
    approved_facilities = [f for f in facilities if f.status.value == "APPROVED"]

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def toggle_active(staff_id: int, is_active: bool):
        try:
            staff_service.set_staff_active(user.user_id, staff_id, is_active)
            ui.notify("Đã cập nhật trạng thái nhân viên.", type="positive")
            refresh()
        except StaffError as e:
            ui.notify(str(e), type="negative")

    def refresh():
        container.clear()
        staff_list = staff_service.list_staff_by_owner(user.user_id)
        with container:
            if not staff_list:
                ui.label("Bạn chưa có nhân viên nào.")
            for s in staff_list:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(s.full_name).classes("font-bold")
                            ui.label(f"SĐT: {s.phone}")
                        active_switch = ui.switch("Đang hoạt động", value=s.is_active)
                        active_switch.on_value_change(lambda e, sid=s.id: toggle_active(sid, e.value))

    def new_staff_dialog():
        if not approved_facilities:
            ui.notify("Bạn cần có ít nhất một cơ sở sân đã được duyệt trước khi thêm nhân viên.", type="warning")
            return
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Thêm nhân viên mới").classes("text-lg font-bold")
            facility_select = ui.select(
                {f.id: f.name for f in approved_facilities},
                value=approved_facilities[0].id,
                label="Cơ sở sân",
            ).classes("w-full")
            full_name = ui.input("Họ và tên").classes("w-full")
            phone = ui.input("Số điện thoại").classes("w-full")
            password = ui.input("Mật khẩu tạm thời", password=True).classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    staff_service.create_staff(
                        owner_id=user.user_id,
                        facility_id=facility_select.value,
                        full_name=full_name.value,
                        phone=phone.value,
                        password=password.value,
                    )
                    dialog.close()
                    refresh()
                    ui.notify("Đã tạo tài khoản nhân viên.", type="positive")
                except StaffError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Tạo tài khoản", on_click=submit)
                ui.button("Hủy", on_click=dialog.close)
        dialog.open()

    ui.button("＋ Thêm nhân viên", on_click=new_staff_dialog).classes("mx-4")
    refresh()


@ui.page("/owner/revenue")
def owner_revenue_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Báo cáo doanh thu (đã thu cọc)").classes("text-2xl font-bold mt-4 mx-4")

    rows = booking_service.revenue_report(user.user_id)
    with ui.column().classes("mx-4 mt-4 gap-2"):
        if not rows:
            ui.label("Chưa có doanh thu nào được ghi nhận.")
        total = 0.0
        for field_name, count, revenue in rows:
            revenue = revenue or 0.0
            total += revenue
            with ui.card().classes("w-96"):
                ui.label(field_name).classes("font-bold")
                ui.label(f"Số lượt đặt (đã cọc): {count}")
                ui.label(f"Doanh thu cọc: {revenue:,.0f} đ")
        if rows:
            ui.label(f"Tổng doanh thu: {total:,.0f} đ").classes("text-lg font-bold mt-2")


@ui.page("/owner/reviews")
def owner_reviews_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Đánh giá của khách hàng").classes("text-2xl font-bold mt-4 mx-4")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def reply_dialog(review_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Phản hồi đánh giá").classes("text-lg font-bold")
            reply = ui.textarea("Nội dung phản hồi").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    review_service.reply_to_review(review_id, user.user_id, reply.value)
                    ui.notify("Đã gửi phản hồi.", type="positive")
                    dialog.close()
                    refresh()
                except ReviewError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Gửi phản hồi", on_click=submit)
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def refresh():
        container.clear()
        reviews = review_service.list_owner_reviews(user.user_id)
        with container:
            if not reviews:
                ui.label("Chưa có đánh giá nào.")
            for r in reviews:
                with ui.card().classes("w-full"):
                    ui.label(f"{'⭐' * r.rating} - Sân #{r.field_id}").classes("font-bold")
                    if r.comment:
                        ui.label(r.comment)
                    if r.owner_reply:
                        ui.label(f"Phản hồi của bạn: {r.owner_reply}").classes("text-sm text-blue-600")
                    else:
                        ui.button("Phản hồi", on_click=lambda rid=r.id: reply_dialog(rid)).props("size=sm")

    refresh()
