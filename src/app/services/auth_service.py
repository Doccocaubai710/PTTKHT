"""Business logic cho UC01 (đăng ký), UC02 (đăng nhập), UC03 (đặt lại mật khẩu)
và UC04 (cập nhật thông tin cá nhân)."""
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.database import get_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository

RESET_CODE_EXPIRE_MINUTES = 15
# Chỉ hai vai trò này được tự đăng ký công khai (UC01); Nhân viên do Chủ sân tạo (UC16),
# Quản trị viên do hệ thống khởi tạo sẵn, không có form đăng ký công khai.
SELF_REGISTER_ROLES = (UserRole.CUSTOMER, UserRole.FIELD_OWNER)


class AuthError(Exception):
    """Lỗi nghiệp vụ khi đăng ký/đăng nhập (số điện thoại đã tồn tại, sai mật khẩu...)."""


@dataclass
class AuthResult:
    token: str
    user_id: int
    full_name: str
    role: UserRole


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.reset_repo = PasswordResetRepository()

    # ---- UC01: đăng ký tài khoản ----
    def register(self, full_name: str, phone: str, password: str, role: UserRole, email: str | None = None) -> AuthResult:
        if not full_name or not phone or not password:
            raise AuthError("Vui lòng nhập đầy đủ họ tên, số điện thoại và mật khẩu.")
        if len(password) < 6:
            raise AuthError("Mật khẩu phải có ít nhất 6 ký tự.")
        if role not in SELF_REGISTER_ROLES:
            raise AuthError("Vai trò này không được phép tự đăng ký.")

        with get_session() as session:
            if self.user_repo.get_by_phone(session, phone):
                raise AuthError("Số điện thoại này đã được đăng ký.")

            user = User(
                full_name=full_name,
                phone=phone,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            self.user_repo.add(session, user)
            token = create_access_token(user.id, user.role.value)
            return AuthResult(token=token, user_id=user.id, full_name=user.full_name, role=user.role)

    # ---- UC02: đăng nhập ----
    def login(self, phone: str, password: str) -> AuthResult:
        with get_session() as session:
            user = self.user_repo.get_by_phone(session, phone)
            if not user or not verify_password(password, user.password_hash):
                raise AuthError("Số điện thoại hoặc mật khẩu không đúng.")
            if not user.is_active:
                raise AuthError("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.")

            token = create_access_token(user.id, user.role.value)
            return AuthResult(token=token, user_id=user.id, full_name=user.full_name, role=user.role)

    # ---- UC03: yêu cầu đặt lại mật khẩu (sinh mã, mô phỏng gửi qua email/SMS) ----
    def request_password_reset(self, phone: str) -> str:
        with get_session() as session:
            user = self.user_repo.get_by_phone(session, phone)
            if not user:
                raise AuthError("Không tìm thấy tài khoản với số điện thoại này.")

            code = "".join(random.choices(string.digits, k=6))
            token = PasswordResetToken(
                user_id=user.id,
                code=code,
                expires_at=datetime.utcnow() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES),
            )
            self.reset_repo.add(session, token)
            # Demo: hệ thống không có dịch vụ gửi email/SMS thật nên trả mã trực tiếp
            # để hiển thị trên UI (mô phỏng nội dung email/SMS khách sẽ nhận được).
            return code

    # ---- UC03: xác nhận mã & đặt mật khẩu mới ----
    def reset_password(self, phone: str, code: str, new_password: str) -> None:
        if len(new_password) < 6:
            raise AuthError("Mật khẩu mới phải có ít nhất 6 ký tự.")
        with get_session() as session:
            user = self.user_repo.get_by_phone(session, phone)
            if not user:
                raise AuthError("Không tìm thấy tài khoản với số điện thoại này.")

            token = self.reset_repo.get_valid(session, user.id, code)
            if not token or token.expires_at < datetime.utcnow():
                raise AuthError("Mã xác nhận không hợp lệ hoặc đã hết hạn.")

            user.password_hash = hash_password(new_password)
            token.used = True

    # ---- UC04: cập nhật thông tin cá nhân ----
    def update_profile(self, user_id: int, full_name: str, email: str | None) -> User:
        if not full_name:
            raise AuthError("Vui lòng nhập họ tên.")
        with get_session() as session:
            user = self.user_repo.get_by_id(session, user_id)
            if not user:
                raise AuthError("Không tìm thấy người dùng.")
            user.full_name = full_name
            user.email = email
            session.flush()
            session.expunge(user)
            return user

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        if len(new_password) < 6:
            raise AuthError("Mật khẩu mới phải có ít nhất 6 ký tự.")
        with get_session() as session:
            user = self.user_repo.get_by_id(session, user_id)
            if not user or not verify_password(current_password, user.password_hash):
                raise AuthError("Mật khẩu hiện tại không đúng.")
            user.password_hash = hash_password(new_password)
