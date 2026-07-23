"""Presentation layer cho UC001 - Đăng ký / Đăng nhập tài khoản."""
from nicegui import app, ui

from app.models.enums import UserRole
from app.pages.guards import home_path_for_role
from app.services.auth_service import AuthError, AuthService

auth_service = AuthService()


def _store_session(result):
    app.storage.user["token"] = result.token
    app.storage.user["user_id"] = result.user_id
    app.storage.user["full_name"] = result.full_name
    app.storage.user["role"] = result.role.value


@ui.page("/login")
def login_page():
    ui.label("Đăng nhập - Hệ thống đặt sân thể thao").classes("text-2xl font-bold mt-8")

    with ui.card().classes("w-96 mx-auto mt-4"):
        phone = ui.input("Số điện thoại").classes("w-full")
        password = ui.input("Mật khẩu", password=True).classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def do_login():
            try:
                result = auth_service.login(phone.value, password.value)
                _store_session(result)
                ui.notify(f"Xin chào {result.full_name}!", type="positive")
                ui.navigate.to(home_path_for_role(result.role))
            except AuthError as e:
                error_label.text = str(e)

        ui.button("Đăng nhập", on_click=do_login).classes("w-full")
        ui.link("Chưa có tài khoản? Đăng ký ngay", "/register")

    with ui.card().classes("w-96 mx-auto mt-4 bg-blue-50"):
        ui.label("Tài khoản demo (mật khẩu: 123456):").classes("font-bold")
        ui.label("Khách hàng : 0900000002")
        ui.label("Chủ sân    : 0900000001")
        ui.label("Nhân viên  : 0900000003")


@ui.page("/register")
def register_page():
    ui.label("Đăng ký tài khoản").classes("text-2xl font-bold mt-8")

    with ui.card().classes("w-96 mx-auto mt-4"):
        full_name = ui.input("Họ và tên").classes("w-full")
        phone = ui.input("Số điện thoại").classes("w-full")
        email = ui.input("Email (tùy chọn)").classes("w-full")
        password = ui.input("Mật khẩu (tối thiểu 6 ký tự)", password=True).classes("w-full")
        role = ui.select(
            {r.value: label for r, label in [
                (UserRole.CUSTOMER, "Khách hàng"),
                (UserRole.FIELD_OWNER, "Chủ sân"),
                (UserRole.STAFF, "Nhân viên"),
            ]},
            value=UserRole.CUSTOMER.value,
            label="Vai trò",
        ).classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def do_register():
            try:
                result = auth_service.register(
                    full_name=full_name.value,
                    phone=phone.value,
                    password=password.value,
                    role=UserRole(role.value),
                    email=email.value or None,
                )
                _store_session(result)
                ui.notify("Đăng ký thành công!", type="positive")
                ui.navigate.to(home_path_for_role(result.role))
            except AuthError as e:
                error_label.text = str(e)

        ui.button("Đăng ký", on_click=do_register).classes("w-full")
        ui.link("Đã có tài khoản? Đăng nhập", "/login")
