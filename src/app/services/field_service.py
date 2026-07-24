"""Business logic cho UC05 (tìm sân), UC06 (xem chi tiết), UC07 (xem lịch trống),
UC14 (quản lý sân & khung giờ) và UC15 (thiết lập giá theo khung giờ)."""
from dataclasses import dataclass
from datetime import date, time

from app.core.database import get_session
from app.models.enums import SportType
from app.models.field import Field, FieldTimeSlot
from app.repositories.booking_repository import BookingRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.field_repository import FieldRepository, FieldTimeSlotRepository


class FieldError(Exception):
    pass


@dataclass
class SlotAvailability:
    slot_id: int
    start_time: time
    end_time: time
    price: float
    is_booked: bool


@dataclass
class FieldSummary:
    """View kết hợp Field + thông tin Cơ sở sân (Facility) để hiển thị cho khách hàng."""

    field_id: int
    name: str
    sport_type: SportType
    description: str | None
    facility_id: int
    facility_name: str
    area: str
    address: str


class FieldService:
    def __init__(self):
        self.field_repo = FieldRepository()
        self.slot_repo = FieldTimeSlotRepository()
        self.booking_repo = BookingRepository()
        self.facility_repo = FacilityRepository()

    # ---- UC05: tìm sân theo khu vực, loại sân (chỉ các sân thuộc cơ sở đã được duyệt) ----
    def search_fields(
        self, area: str | None = None, sport_type: SportType | None = None, approved_only: bool = True
    ) -> list[FieldSummary]:
        with get_session() as session:
            fields = self.field_repo.search(
                session, area=area, sport_type=sport_type, approved_only=approved_only
            )
            return [self._to_summary(f) for f in fields]

    def _to_summary(self, field: Field) -> FieldSummary:
        facility = field.facility
        return FieldSummary(
            field_id=field.id,
            name=field.name,
            sport_type=field.sport_type,
            description=field.description,
            facility_id=facility.id,
            facility_name=facility.name,
            area=facility.area,
            address=facility.address,
        )

    # ---- UC06: xem chi tiết sân (kèm thông tin Cơ sở sân) ----
    def get_field_summary(self, field_id: int) -> FieldSummary | None:
        with get_session() as session:
            field = self.field_repo.get_by_id(session, field_id)
            return self._to_summary(field) if field else None

    # ---- UC07: xem lịch trống theo khung giờ thực ----
    def get_availability(self, field_id: int, on_date: date) -> list[SlotAvailability]:
        with get_session() as session:
            slots = self.slot_repo.list_by_field(session, field_id, active_only=True)
            booked_slot_ids = self.booking_repo.list_booked_slot_ids(session, field_id, on_date)
            return [
                SlotAvailability(
                    slot_id=s.id,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    price=s.price,
                    is_booked=s.id in booked_slot_ids,
                )
                for s in slots
            ]

    # ---- UC06: xem chi tiết sân ----
    def get_field(self, field_id: int) -> Field | None:
        with get_session() as session:
            field = self.field_repo.get_by_id(session, field_id)
            if field:
                session.expunge(field)
            return field

    # ---- UC14: Chủ sân đăng ký một Sân mới thuộc một Cơ sở sân của mình ----
    def create_field(
        self, owner_id: int, facility_id: int, name: str, sport_type: SportType, description: str | None = None
    ) -> Field:
        if not name:
            raise FieldError("Vui lòng nhập tên sân.")
        with get_session() as session:
            facility = self.facility_repo.get_by_id(session, facility_id)
            if not facility or facility.owner_id != owner_id:
                raise FieldError("Cơ sở sân không hợp lệ.")

            field = Field(
                facility_id=facility_id,
                name=name,
                sport_type=sport_type,
                description=description,
            )
            self.field_repo.add(session, field)
            session.expunge(field)
            return field

    def list_owner_fields(self, owner_id: int) -> list[Field]:
        with get_session() as session:
            fields = self.field_repo.list_by_owner(session, owner_id)
            session.expunge_all()
            return fields

    def list_facility_fields(self, facility_id: int) -> list[Field]:
        with get_session() as session:
            fields = self.field_repo.list_by_facility(session, facility_id)
            session.expunge_all()
            return fields

    # ---- UC14 + UC15: quản lý khung giờ & giá sân ----
    def add_time_slot(self, field_id: int, start_time: time, end_time: time, price: float) -> FieldTimeSlot:
        if start_time >= end_time:
            raise FieldError("Giờ bắt đầu phải trước giờ kết thúc.")
        if price <= 0:
            raise FieldError("Giá sân phải lớn hơn 0.")
        with get_session() as session:
            slot = FieldTimeSlot(field_id=field_id, start_time=start_time, end_time=end_time, price=price)
            self.slot_repo.add(session, slot)
            session.expunge(slot)
            return slot

    def update_time_slot_price(self, slot_id: int, price: float) -> None:
        if price <= 0:
            raise FieldError("Giá sân phải lớn hơn 0.")
        with get_session() as session:
            slot = self.slot_repo.get_by_id(session, slot_id)
            if not slot:
                raise FieldError("Không tìm thấy khung giờ.")
            slot.price = price

    def set_time_slot_active(self, slot_id: int, is_active: bool) -> None:
        with get_session() as session:
            slot = self.slot_repo.get_by_id(session, slot_id)
            if not slot:
                raise FieldError("Không tìm thấy khung giờ.")
            slot.is_active = is_active

    def list_time_slots(self, field_id: int) -> list[FieldTimeSlot]:
        with get_session() as session:
            slots = self.slot_repo.list_by_field(session, field_id)
            session.expunge_all()
            return slots
