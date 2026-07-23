"""Business logic cho UC001 - Đăng ký / Đăng nhập tài khoản."""
from dataclasses import dataclass

from app.core.database import get_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


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

    def register(self, full_name: str, phone: str, password: str, role: UserRole, email: str | None = None) -> AuthResult:
        if not full_name or not phone or not password:
            raise AuthError("Vui lòng nhập đầy đủ họ tên, số điện thoại và mật khẩu.")
        if len(password) < 6:
            raise AuthError("Mật khẩu phải có ít nhất 6 ký tự.")

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

    def login(self, phone: str, password: str) -> AuthResult:
        with get_session() as session:
            user = self.user_repo.get_by_phone(session, phone)
            if not user or not verify_password(password, user.password_hash):
                raise AuthError("Số điện thoại hoặc mật khẩu không đúng.")

            token = create_access_token(user.id, user.role.value)
            return AuthResult(token=token, user_id=user.id, full_name=user.full_name, role=user.role)
