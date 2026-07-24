"""Presentation-layer helper: đọc JWT từ phiên trình duyệt (app.storage.user)
và điều hướng theo role. Đây là nơi 'route/controller' của kiến trúc 3 lớp
kiểm tra quyền truy cập trước khi hiển thị trang, tương tự middleware auth
của một REST API thông thường.
"""
from dataclasses import dataclass

from nicegui import app, ui

from app.core.security import decode_access_token
from app.models.enums import UserRole


@dataclass
class CurrentUser:
    user_id: int
    role: UserRole
    full_name: str


def get_current_user() -> CurrentUser | None:
    token = app.storage.user.get("token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return CurrentUser(
        user_id=int(payload["sub"]),
        role=UserRole(payload["role"]),
        full_name=app.storage.user.get("full_name", ""),
    )


def require_login() -> CurrentUser | None:
    """Trả về user hiện tại, hoặc điều hướng về /login và trả None nếu chưa đăng nhập."""
    user = get_current_user()
    if not user:
        ui.navigate.to("/login")
        return None
    return user


def require_role(*roles: UserRole) -> CurrentUser | None:
    user = require_login()
    if user is None:
        return None
    if user.role not in roles:
        ui.notify("Bạn không có quyền truy cập trang này.", type="negative")
        ui.navigate.to("/")
        return None
    return user


def home_path_for_role(role: UserRole) -> str:
    return {
        UserRole.CUSTOMER: "/search",
        UserRole.FIELD_OWNER: "/owner",
        UserRole.STAFF: "/staff",
        UserRole.ADMIN: "/admin",
    }[role]


def logout():
    app.storage.user.clear()
    ui.navigate.to("/login")
