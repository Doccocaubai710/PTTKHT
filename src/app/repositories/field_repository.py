"""Data Access layer cho Field và FieldTimeSlot."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SportType
from app.models.field import Field, FieldTimeSlot


class FieldRepository:
    def get_by_id(self, session: Session, field_id: int) -> Field | None:
        return session.get(Field, field_id)

    def list_by_owner(self, session: Session, owner_id: int) -> list[Field]:
        stmt = select(Field).where(Field.owner_id == owner_id)
        return list(session.execute(stmt).scalars().all())

    def search(
        self,
        session: Session,
        area: str | None = None,
        sport_type: SportType | None = None,
    ) -> list[Field]:
        stmt = select(Field)
        if area:
            stmt = stmt.where(Field.area.ilike(f"%{area}%"))
        if sport_type:
            stmt = stmt.where(Field.sport_type == sport_type)
        return list(session.execute(stmt).scalars().all())

    def add(self, session: Session, field: Field) -> Field:
        session.add(field)
        session.flush()
        return field


class FieldTimeSlotRepository:
    def get_by_id(self, session: Session, slot_id: int) -> FieldTimeSlot | None:
        return session.get(FieldTimeSlot, slot_id)

    def list_by_field(self, session: Session, field_id: int, active_only: bool = False) -> list[FieldTimeSlot]:
        stmt = select(FieldTimeSlot).where(FieldTimeSlot.field_id == field_id)
        if active_only:
            stmt = stmt.where(FieldTimeSlot.is_active.is_(True))
        stmt = stmt.order_by(FieldTimeSlot.start_time)
        return list(session.execute(stmt).scalars().all())

    def add(self, session: Session, slot: FieldTimeSlot) -> FieldTimeSlot:
        session.add(slot)
        session.flush()
        return slot

    def delete(self, session: Session, slot: FieldTimeSlot) -> None:
        session.delete(slot)
