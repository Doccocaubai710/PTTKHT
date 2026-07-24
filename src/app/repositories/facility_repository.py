"""Data Access layer cho Facility (Cơ sở sân)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FacilityStatus
from app.models.facility import Facility


class FacilityRepository:
    def get_by_id(self, session: Session, facility_id: int) -> Facility | None:
        return session.get(Facility, facility_id)

    def add(self, session: Session, facility: Facility) -> Facility:
        session.add(facility)
        session.flush()
        return facility

    def list_by_owner(self, session: Session, owner_id: int) -> list[Facility]:
        stmt = select(Facility).where(Facility.owner_id == owner_id).order_by(Facility.created_at.desc())
        return list(session.execute(stmt).scalars().all())

    def list_by_status(self, session: Session, status: FacilityStatus) -> list[Facility]:
        stmt = select(Facility).where(Facility.status == status).order_by(Facility.created_at.desc())
        return list(session.execute(stmt).scalars().all())

    def list_approved(self, session: Session, area: str | None = None) -> list[Facility]:
        stmt = select(Facility).where(Facility.status == FacilityStatus.APPROVED)
        if area:
            stmt = stmt.where(Facility.area.ilike(f"%{area}%"))
        return list(session.execute(stmt).scalars().all())

    def list_all(self, session: Session) -> list[Facility]:
        stmt = select(Facility).order_by(Facility.created_at.desc())
        return list(session.execute(stmt).scalars().all())
