"""Thành phần giao diện dùng chung: thanh điều hướng theo role."""
from nicegui import ui

from app.pages.guards import CurrentUser, logout


def header(user: CurrentUser, links: list[tuple[str, str]]):
    with ui.header().classes("items-center justify-between"):
        with ui.row().classes("items-center gap-4"):
            ui.label("🏟 Đặt sân thể thao").classes("text-lg font-bold")
            for text, path in links:
                ui.link(text, path).classes("text-white")
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
    "CONFIRMED": "Đã xác nhận",
    "COMPLETED": "Đã hoàn thành",
    "CANCELLED": "Đã hủy",
    "EXPIRED": "Đã hết hạn giữ chỗ",
}

STATUS_COLORS = {
    "PENDING": "orange",
    "CONFIRMED": "blue",
    "COMPLETED": "green",
    "CANCELLED": "grey",
    "EXPIRED": "red",
}
