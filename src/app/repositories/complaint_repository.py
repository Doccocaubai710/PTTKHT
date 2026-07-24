from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus


class ComplaintRepository:
    def get_by_id(self, session: Session, complaint_id: int) -> Complaint | None:
        return session.get(Complaint, complaint_id)

    def add(self, session: Session, complaint: Complaint) -> Complaint:
        session.add(complaint)
        session.flush()
        return complaint

    def list_by_user(self, session: Session, user_id: int) -> list[Complaint]:
        stmt = (
            select(Complaint)
            .where(Complaint.created_by_id == user_id)
            .order_by(Complaint.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())

    def list_all(self, session: Session, status: ComplaintStatus | None = None) -> list[Complaint]:
        stmt = select(Complaint).order_by(Complaint.created_at.desc())
        if status:
            stmt = stmt.where(Complaint.status == status)
        return list(session.execute(stmt).scalars().all())
