"""Business logic cho UC16 - Chủ sân quản lý tài khoản nhân viên của cơ sở mình."""
from app.core.database import get_session
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.facility_repository import FacilityRepository
from app.repositories.user_repository import UserRepository


class StaffError(Exception):
    pass


class StaffService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.facility_repo = FacilityRepository()

    def create_staff(
        self, owner_id: int, facility_id: int, full_name: str, phone: str, password: str, email: str | None = None
    ) -> User:
        if not full_name or not phone or not password:
            raise StaffError("Vui lòng nhập đầy đủ họ tên, số điện thoại và mật khẩu.")
        if len(password) < 6:
            raise StaffError("Mật khẩu phải có ít nhất 6 ký tự.")

        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if not facility or facility.owner_id != owner_id:
                raise StaffError("Cơ sở sân không hợp lệ.")

            if self.user_repo.get_by_phone(session, phone):
                raise StaffError("Số điện thoại này đã được đăng ký.")

            staff = User(
                full_name=full_name,
                phone=phone,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.STAFF,
                facility_id=facility_id,
            )
            self.user_repo.add(session, staff)
            session.expunge(staff)
            return staff

    def list_staff_by_owner(self, owner_id: int) -> list[User]:
        with get_session() as session:
            facilities = self.facility_repo.list_by_owner(session, owner_id)
            facility_ids = {f.id for f in facilities}
            staff: list[User] = []
            for fid in facility_ids:
                staff.extend(self.user_repo.list_by_facility(session, fid))
            session.expunge_all()
            return staff

    def set_staff_active(self, owner_id: int, staff_id: int, is_active: bool) -> None:
        with get_session() as session:
            staff = self.user_repo.get_by_id(session, staff_id)
            if not staff or staff.role != UserRole.STAFF:
                raise StaffError("Không tìm thấy nhân viên.")
            facility = self.facility_repo.get_by_id(session, staff.facility_id) if staff.facility_id else None
            if not facility or facility.owner_id != owner_id:
                raise StaffError("Bạn không có quyền quản lý nhân viên này.")
            staff.is_active = is_active
