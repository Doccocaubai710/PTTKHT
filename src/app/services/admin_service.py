"""Business logic cho UC25 (quản lý tài khoản toàn hệ thống) và UC26 (thống kê/giám sát)."""
from app.core.database import get_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.user_repository import UserRepository


class AdminError(Exception):
    pass


class AdminService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.facility_repo = FacilityRepository()
        self.booking_repo = BookingRepository()

    # ---- UC25: quản lý tài khoản người dùng trên toàn hệ thống ----
    def list_users(self, role: UserRole | None = None) -> list[User]:
        with get_session() as session:
            users = (
                self.user_repo.list_by_role(session, role) if role else self.user_repo.list_all(session)
            )
            session.expunge_all()
            return users

    def set_user_active(self, admin_id: int, user_id: int, is_active: bool) -> User:
        with get_session() as session:
            user = self.user_repo.get_by_id(session, user_id)
            if not user:
                raise AdminError("Không tìm thấy người dùng.")
            if user.role == UserRole.ADMIN and user.id != admin_id:
                raise AdminError("Không thể khóa tài khoản quản trị viên khác.")
            user.is_active = is_active
            session.flush()
            session.expunge(user)
            return user

    # ---- UC26: thống kê, giám sát hoạt động của toàn hệ thống ----
    def system_overview(self) -> dict:
        with get_session() as session:
            users = self.user_repo.list_all(session)
            by_role: dict[str, int] = {}
            for u in users:
                by_role[u.role.value] = by_role.get(u.role.value, 0) + 1

            facilities = self.facility_repo.list_all(session)
            facility_by_status: dict[str, int] = {}
            for f in facilities:
                facility_by_status[f.status.value] = facility_by_status.get(f.status.value, 0) + 1

            booking_stats = self.booking_repo.system_stats(session)

            return {
                "total_users": len(users),
                "users_by_role": by_role,
                "total_facilities": len(facilities),
                "facilities_by_status": facility_by_status,
                "total_bookings": booking_stats["total_bookings"],
                "total_revenue": booking_stats["total_revenue"],
                "bookings_by_status": {k.value: v for k, v in booking_stats["by_status"].items()},
            }
