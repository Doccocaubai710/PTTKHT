"""Business logic cho UC13 (đăng ký/cập nhật cơ sở sân) và UC24 (duyệt cơ sở sân mới)."""
from datetime import datetime

from app.core.database import get_session
from app.models.enums import FacilityStatus
from app.models.facility import Facility
from app.repositories.facility_repository import FacilityRepository


class FacilityError(Exception):
    pass


class FacilityService:
    def __init__(self):
        self.facility_repo = FacilityRepository()

    # ---- UC13: Chủ sân đăng ký cơ sở sân mới (mặc định "chờ duyệt") ----
    def register_facility(
        self,
        owner_id: int,
        name: str,
        area: str,
        address: str,
        description: str | None = None,
        cancellation_policy: str | None = None,
    ) -> Facility:
        if not name or not area or not address:
            raise FacilityError("Vui lòng nhập đầy đủ tên cơ sở, khu vực và địa chỉ.")
        with get_session() as session:
            facility = Facility(
                owner_id=owner_id,
                name=name,
                area=area,
                address=address,
                description=description,
                cancellation_policy=cancellation_policy,
                status=FacilityStatus.PENDING,
            )
            self.facility_repo.add(session, facility)
            session.expunge(facility)
            return facility

    # ---- UC13: Chủ sân cập nhật thông tin cơ sở sân (bị từ chối -> chỉnh sửa & gửi lại) ----
    def update_facility(
        self,
        facility_id: int,
        owner_id: int,
        name: str,
        area: str,
        address: str,
        description: str | None = None,
        cancellation_policy: str | None = None,
    ) -> Facility:
        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if not facility or facility.owner_id != owner_id:
                raise FacilityError("Không tìm thấy cơ sở sân.")

            facility.name = name
            facility.area = area
            facility.address = address
            facility.description = description
            facility.cancellation_policy = cancellation_policy
            if facility.status == FacilityStatus.REJECTED:
                # gửi lại hồ sơ đã chỉnh sửa để quản trị viên duyệt lại
                facility.status = FacilityStatus.PENDING
                facility.reject_reason = None

            session.flush()
            session.expunge(facility)
            return facility

    def get_facility(self, facility_id: int) -> Facility | None:
        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if facility:
                session.expunge(facility)
            return facility

    def list_owner_facilities(self, owner_id: int) -> list[Facility]:
        with get_session() as session:
            facilities = self.facility_repo.list_by_owner(session, owner_id)
            session.expunge_all()
            return facilities

    def search_public_facilities(self, area: str | None = None) -> list[Facility]:
        with get_session() as session:
            facilities = self.facility_repo.list_approved(session, area=area)
            session.expunge_all()
            return facilities

    # ---- UC24: Quản trị viên duyệt / từ chối cơ sở sân mới ----
    def list_pending_facilities(self) -> list[Facility]:
        with get_session() as session:
            facilities = self.facility_repo.list_by_status(session, FacilityStatus.PENDING)
            session.expunge_all()
            return facilities

    def list_all_facilities(self) -> list[Facility]:
        with get_session() as session:
            facilities = self.facility_repo.list_all(session)
            session.expunge_all()
            return facilities

    def approve_facility(self, facility_id: int, admin_id: int) -> Facility:
        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if not facility:
                raise FacilityError("Không tìm thấy cơ sở sân.")
            if facility.status != FacilityStatus.PENDING:
                raise FacilityError("Cơ sở sân này không ở trạng thái chờ duyệt.")

            facility.status = FacilityStatus.APPROVED
            facility.reviewed_by_id = admin_id
            facility.reviewed_at = datetime.utcnow()
            facility.reject_reason = None

            session.flush()
            session.expunge(facility)
            return facility

    def reject_facility(self, facility_id: int, admin_id: int, reason: str) -> Facility:
        if not reason:
            raise FacilityError("Vui lòng nêu rõ lý do từ chối.")
        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if not facility:
                raise FacilityError("Không tìm thấy cơ sở sân.")
            if facility.status != FacilityStatus.PENDING:
                raise FacilityError("Cơ sở sân này không ở trạng thái chờ duyệt.")

            facility.status = FacilityStatus.REJECTED
            facility.reviewed_by_id = admin_id
            facility.reviewed_at = datetime.utcnow()
            facility.reject_reason = reason

            session.flush()
            session.expunge(facility)
            return facility
