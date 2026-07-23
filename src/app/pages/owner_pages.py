"""Presentation layer cho UC006 - Quản lý khung giờ & giá sân (+ đăng ký sân, xem doanh thu)."""
from datetime import time

from nicegui import ui

from app.models.enums import SportType, UserRole
from app.pages.common import SPORT_TYPE_LABELS, header
from app.pages.guards import require_role
from app.services.field_service import FieldError, FieldService
from app.services.booking_service import BookingService

field_service = FieldService()
booking_service = BookingService()


@ui.page("/owner")
def owner_dashboard_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, [("Sân của tôi", "/owner"), ("Doanh thu", "/owner/revenue")])
    ui.label("Quản lý sân").classes("text-2xl font-bold mt-4 mx-4")

    fields_container = ui.column().classes("mx-4 mt-4 w-full gap-4")

    def refresh():
        fields_container.clear()
        fields = field_service.list_owner_fields(user.user_id)
        with fields_container:
            for f in fields:
                with ui.card().classes("w-full"):
                    ui.label(f"{f.name} ({SPORT_TYPE_LABELS[f.sport_type.value]}) - {f.area}").classes(
                        "text-lg font-bold"
                    )
                    slots = field_service.list_time_slots(f.id)
                    with ui.column().classes("gap-1 mt-2"):
                        for s in slots:
                            with ui.row().classes("items-center gap-4"):
                                ui.label(f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}").classes(
                                    "w-32"
                                )
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

    ui.button("＋ Đăng ký sân mới", on_click=lambda: new_field_dialog(refresh)).classes("mx-4")
    refresh()


def new_field_dialog(on_created):
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Đăng ký sân mới").classes("text-lg font-bold")
        name = ui.input("Tên sân").classes("w-full")
        sport = ui.select(
            {s.value: SPORT_TYPE_LABELS[s.value] for s in SportType}, value=SportType.FOOTBALL.value, label="Loại sân"
        ).classes("w-full")
        area = ui.input("Khu vực").classes("w-full")
        address = ui.input("Địa chỉ").classes("w-full")
        description = ui.textarea("Mô tả (tùy chọn)").classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def submit():
            try:
                field_service.create_field(
                    owner_id=user.user_id,
                    name=name.value,
                    sport_type=SportType(sport.value),
                    area=area.value,
                    address=address.value,
                    description=description.value or None,
                )
                dialog.close()
                on_created()
                ui.notify("Đăng ký sân thành công.", type="positive")
            except FieldError as e:
                error_label.text = str(e)

        with ui.row():
            ui.button("Lưu", on_click=submit)
            ui.button("Hủy", on_click=dialog.close)
    dialog.open()


@ui.page("/owner/revenue")
def owner_revenue_page():
    user = require_role(UserRole.FIELD_OWNER)
    if not user:
        return

    header(user, [("Sân của tôi", "/owner"), ("Doanh thu", "/owner/revenue")])
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
