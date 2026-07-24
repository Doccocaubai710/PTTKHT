"""Presentation layer cho UC01 (đăng ký), UC02 (đăng nhập), UC03 (đặt lại mật khẩu)
và UC04 (cập nhật thông tin cá nhân)."""
from nicegui import app, ui

from app.models.enums import UserRole
from app.pages.guards import home_path_for_role, require_login
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
        with ui.row().classes("w-full justify-between"):
            ui.link("Chưa có tài khoản? Đăng ký ngay", "/register")
            ui.link("Quên mật khẩu?", "/forgot-password")

    with ui.card().classes("w-96 mx-auto mt-4 bg-blue-50"):
        ui.label("Tài khoản demo (mật khẩu: 123456):").classes("font-bold")
        ui.label("Khách hàng   : 0900000002")
        ui.label("Chủ sân      : 0900000001")
        ui.label("Nhân viên    : 0900000003")
        ui.label("Quản trị viên: 0900000004")


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
            ]},
            value=UserRole.CUSTOMER.value,
            label="Vai trò",
        ).classes("w-full")
        ui.label(
            "Tài khoản Nhân viên do Chủ sân tạo trong trang quản lý nhân viên."
        ).classes("text-xs text-gray-500")
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


@ui.page("/forgot-password")
def forgot_password_page():
    ui.label("Quên mật khẩu").classes("text-2xl font-bold mt-8")

    with ui.card().classes("w-96 mx-auto mt-4"):
        ui.label("Nhập số điện thoại đã đăng ký để nhận mã đặt lại mật khẩu.")
        phone = ui.input("Số điện thoại").classes("w-full")
        error_label = ui.label("").classes("text-red-500")
        code_label = ui.label("").classes("text-green-600 font-bold")

        def request_code():
            try:
                code = auth_service.request_password_reset(phone.value)
                # Demo: không có dịch vụ email/SMS thật nên hiển thị mã trực tiếp tại đây.
                code_label.text = f"(Demo) Mã xác nhận đã 'gửi' tới bạn: {code}"
                error_label.text = ""
            except AuthError as e:
                error_label.text = str(e)
                code_label.text = ""

        ui.button("Gửi mã xác nhận", on_click=request_code).classes("w-full")
        ui.link("Đã có mã? Đặt lại mật khẩu", "/reset-password")
        ui.link("Quay lại đăng nhập", "/login")


@ui.page("/reset-password")
def reset_password_page():
    ui.label("Đặt lại mật khẩu").classes("text-2xl font-bold mt-8")

    with ui.card().classes("w-96 mx-auto mt-4"):
        phone = ui.input("Số điện thoại").classes("w-full")
        code = ui.input("Mã xác nhận").classes("w-full")
        new_password = ui.input("Mật khẩu mới (tối thiểu 6 ký tự)", password=True).classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def do_reset():
            try:
                auth_service.reset_password(phone.value, code.value, new_password.value)
                ui.notify("Đặt lại mật khẩu thành công, vui lòng đăng nhập lại.", type="positive")
                ui.navigate.to("/login")
            except AuthError as e:
                error_label.text = str(e)

        ui.button("Đặt lại mật khẩu", on_click=do_reset).classes("w-full")
        ui.link("Quay lại đăng nhập", "/login")


@ui.page("/profile")
def profile_page():
    user = require_login()
    if not user:
        return

    from app.repositories.user_repository import UserRepository
    from app.core.database import get_session

    with get_session() as session:
        db_user = UserRepository().get_by_id(session, user.user_id)
        current_name = db_user.full_name
        current_email = db_user.email or ""

    ui.label("Thông tin cá nhân").classes("text-2xl font-bold mt-8 mx-auto w-96")

    with ui.card().classes("w-96 mx-auto mt-4"):
        ui.label(f"Vai trò: {user.role.value}").classes("text-sm text-gray-500")
        full_name = ui.input("Họ và tên", value=current_name).classes("w-full")
        email = ui.input("Email", value=current_email).classes("w-full")
        error_label = ui.label("").classes("text-red-500")

        def save_profile():
            try:
                result = auth_service.update_profile(user.user_id, full_name.value, email.value or None)
                app.storage.user["full_name"] = result.full_name
                ui.notify("Đã cập nhật thông tin cá nhân.", type="positive")
                ui.navigate.reload()
            except AuthError as e:
                error_label.text = str(e)

        ui.button("Lưu thay đổi", on_click=save_profile).classes("w-full")

    with ui.card().classes("w-96 mx-auto mt-4"):
        ui.label("Đổi mật khẩu").classes("font-bold")
        current_password = ui.input("Mật khẩu hiện tại", password=True).classes("w-full")
        new_password = ui.input("Mật khẩu mới (tối thiểu 6 ký tự)", password=True).classes("w-full")
        pw_error_label = ui.label("").classes("text-red-500")

        def change_password():
            try:
                auth_service.change_password(user.user_id, current_password.value, new_password.value)
                ui.notify("Đã đổi mật khẩu thành công.", type="positive")
                current_password.value = ""
                new_password.value = ""
            except AuthError as e:
                pw_error_label.text = str(e)

        ui.button("Đổi mật khẩu", on_click=change_password).classes("w-full")
