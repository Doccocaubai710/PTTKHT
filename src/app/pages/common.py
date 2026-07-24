"""Thành phần giao diện dùng chung: thanh điều hướng theo role."""
from nicegui import ui

from app.pages.guards import CurrentUser, logout


def header(user: CurrentUser, links: list[tuple[str, str]]):
    with ui.header().classes("items-center justify-between"):
        with ui.row().classes("items-center gap-4"):
            ui.label("🏟 Đặt sân thể thao").classes("text-lg font-bold")
            for text, path in links:
                ui.link(text, path).classes("text-white")
            ui.link("Tài khoản", "/profile").classes("text-white")
        with ui.row().classes("items-center gap-4"):
            ui.label(f"{user.full_name} ({user.role.value})")
            ui.button("Đăng xuất", on_click=logout).props("flat color=white")


SPORT_TYPE_LABELS = {
    "FOOTBALL": "Bóng đá mini",
    "BADMINTON": "Cầu lông",
    "TENNIS": "Tennis",
}

STATUS_LABELS = {
    "PENDING": "Chờ thanh toán",
    "AWAITING_CONFIRMATION": "Chờ xác nhận",
    "CONFIRMED": "Đã xác nhận",
    "COMPLETED": "Đã hoàn thành",
    "CANCELLED": "Đã hủy",
    "EXPIRED": "Đã hết hạn giữ chỗ",
}

STATUS_COLORS = {
    "PENDING": "orange",
    "AWAITING_CONFIRMATION": "purple",
    "CONFIRMED": "blue",
    "COMPLETED": "green",
    "CANCELLED": "grey",
    "EXPIRED": "red",
}

FACILITY_STATUS_LABELS = {
    "PENDING": "Chờ duyệt",
    "APPROVED": "Đã duyệt",
    "REJECTED": "Bị từ chối",
}

FACILITY_STATUS_COLORS = {
    "PENDING": "orange",
    "APPROVED": "green",
    "REJECTED": "red",
}

COMPLAINT_STATUS_LABELS = {
    "OPEN": "Mới gửi",
    "IN_PROGRESS": "Đang xử lý",
    "RESOLVED": "Đã giải quyết",
    "REJECTED": "Bị từ chối",
}

COMPLAINT_STATUS_COLORS = {
    "OPEN": "orange",
    "IN_PROGRESS": "blue",
    "RESOLVED": "green",
    "REJECTED": "grey",
}
