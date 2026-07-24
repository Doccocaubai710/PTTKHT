"""Presentation layer cho UC24 (duyệt cơ sở sân mới), UC25 (quản lý tài khoản toàn hệ thống),
UC26 (thống kê/giám sát hệ thống) và UC27 (xử lý khiếu nại/tranh chấp)."""
from app.models.enums import ComplaintStatus, UserRole
from app.pages.common import COMPLAINT_STATUS_COLORS, COMPLAINT_STATUS_LABELS, header
from app.pages.guards import require_role
from app.services.admin_service import AdminError, AdminService
from app.services.complaint_service import ComplaintError, ComplaintService
from app.services.facility_service import FacilityError, FacilityService
from nicegui import ui

facility_service = FacilityService()
admin_service = AdminService()
complaint_service = ComplaintService()

NAV_LINKS = [
    ("Duyệt cơ sở", "/admin"),
    ("Tài khoản", "/admin/users"),
    ("Thống kê", "/admin/stats"),
    ("Khiếu nại", "/admin/complaints"),
]


@ui.page("/admin")
def admin_facilities_page():
    user = require_role(UserRole.ADMIN)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Duyệt đăng ký cơ sở sân mới").classes("text-2xl font-bold mt-4 mx-4")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def reject_dialog(facility_id: int):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Từ chối cơ sở sân").classes("text-lg font-bold")
            reason = ui.input("Lý do từ chối").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    facility_service.reject_facility(facility_id, user.user_id, reason.value)
                    ui.notify("Đã từ chối hồ sơ.", type="warning")
                    dialog.close()
                    refresh()
                except FacilityError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Từ chối", on_click=submit).props("color=negative")
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def approve(facility_id: int):
        try:
            facility_service.approve_facility(facility_id, user.user_id)
            ui.notify("Đã duyệt, cơ sở sân được hiển thị công khai.", type="positive")
            refresh()
        except FacilityError as e:
            ui.notify(str(e), type="negative")

    def refresh():
        container.clear()
        pending = facility_service.list_pending_facilities()
        with container:
            if not pending:
                ui.label("Không có cơ sở sân nào đang chờ duyệt.")
            for f in pending:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f.name).classes("font-bold")
                            ui.label(f"{f.area} • {f.address}")
                            if f.description:
                                ui.label(f.description).classes("text-sm text-gray-500")
                        with ui.row():
                            ui.button("Duyệt", on_click=lambda fid=f.id: approve(fid))
                            ui.button("Từ chối", on_click=lambda fid=f.id: reject_dialog(fid)).props(
                                "color=negative"
                            )

    refresh()


@ui.page("/admin/users")
def admin_users_page():
    user = require_role(UserRole.ADMIN)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Quản lý tài khoản người dùng").classes("text-2xl font-bold mt-4 mx-4")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def toggle_active(user_id: int, is_active: bool):
        try:
            admin_service.set_user_active(user.user_id, user_id, is_active)
            ui.notify("Đã cập nhật trạng thái tài khoản.", type="positive")
        except AdminError as e:
            ui.notify(str(e), type="negative")

    def refresh():
        container.clear()
        users = admin_service.list_users()
        with container:
            for u in users:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(f"{u.full_name} ({u.role.value})").classes("font-bold")
                            ui.label(f"SĐT: {u.phone} | Email: {u.email or '-'}")
                        active_switch = ui.switch("Hoạt động", value=u.is_active)
                        active_switch.on_value_change(lambda e, uid=u.id: toggle_active(uid, e.value))

    refresh()


@ui.page("/admin/stats")
def admin_stats_page():
    user = require_role(UserRole.ADMIN)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Thống kê, giám sát hệ thống").classes("text-2xl font-bold mt-4 mx-4")

    overview = admin_service.system_overview()

    with ui.row().classes("mx-4 mt-4 gap-4 flex-wrap"):
        with ui.card().classes("w-64"):
            ui.label("Tổng người dùng").classes("text-sm text-gray-500")
            ui.label(str(overview["total_users"])).classes("text-3xl font-bold")
            for role, count in overview["users_by_role"].items():
                ui.label(f"{role}: {count}").classes("text-sm")

        with ui.card().classes("w-64"):
            ui.label("Cơ sở sân").classes("text-sm text-gray-500")
            ui.label(str(overview["total_facilities"])).classes("text-3xl font-bold")
            for status, count in overview["facilities_by_status"].items():
                ui.label(f"{status}: {count}").classes("text-sm")

        with ui.card().classes("w-64"):
            ui.label("Đặt sân").classes("text-sm text-gray-500")
            ui.label(str(overview["total_bookings"])).classes("text-3xl font-bold")
            for status, count in overview["bookings_by_status"].items():
                ui.label(f"{status}: {count}").classes("text-sm")

        with ui.card().classes("w-64"):
            ui.label("Tổng doanh thu (cọc đã thu)").classes("text-sm text-gray-500")
            ui.label(f"{overview['total_revenue']:,.0f} đ").classes("text-2xl font-bold")


@ui.page("/admin/complaints")
def admin_complaints_page():
    user = require_role(UserRole.ADMIN)
    if not user:
        return

    header(user, NAV_LINKS)
    ui.label("Khiếu nại / tranh chấp").classes("text-2xl font-bold mt-4 mx-4")

    container = ui.column().classes("mx-4 mt-4 w-full gap-2")

    def resolve_dialog(complaint_id: int, status: ComplaintStatus):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Ghi chú xử lý").classes("text-lg font-bold")
            note = ui.textarea("Nội dung phản hồi / kết quả xử lý").classes("w-full")
            error_label = ui.label("").classes("text-red-500")

            def submit():
                try:
                    complaint_service.resolve_complaint(complaint_id, user.user_id, status, note.value)
                    ui.notify("Đã cập nhật kết quả xử lý.", type="positive")
                    dialog.close()
                    refresh()
                except ComplaintError as e:
                    error_label.text = str(e)

            with ui.row():
                ui.button("Lưu", on_click=submit)
                ui.button("Đóng", on_click=dialog.close)
        dialog.open()

    def refresh():
        container.clear()
        complaints = complaint_service.list_all_complaints()
        with container:
            if not complaints:
                ui.label("Chưa có khiếu nại nào.")
            for c in complaints:
                with ui.card().classes("w-full"):
                    with ui.row().classes("justify-between items-center w-full"):
                        with ui.column():
                            ui.label(c.subject).classes("font-bold")
                            ui.label(c.description).classes("text-sm")
                            if c.resolution_note:
                                ui.label(f"Ghi chú xử lý: {c.resolution_note}").classes("text-sm text-blue-600")
                        with ui.column().classes("items-end gap-1"):
                            ui.badge(COMPLAINT_STATUS_LABELS[c.status.value]).props(
                                f"color={COMPLAINT_STATUS_COLORS[c.status.value]}"
                            )
                            if c.status in (ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS):
                                with ui.row():
                                    ui.button(
                                        "Đang xử lý",
                                        on_click=lambda cid=c.id: resolve_dialog(cid, ComplaintStatus.IN_PROGRESS),
                                    ).props("size=sm flat")
                                    ui.button(
                                        "Giải quyết",
                                        on_click=lambda cid=c.id: resolve_dialog(cid, ComplaintStatus.RESOLVED),
                                    ).props("size=sm")
                                    ui.button(
                                        "Từ chối",
                                        on_click=lambda cid=c.id: resolve_dialog(cid, ComplaintStatus.REJECTED),
                                    ).props("size=sm color=negative")

    refresh()
