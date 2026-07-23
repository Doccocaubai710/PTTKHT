from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def get_by_booking(self, session: Session, booking_id: int) -> Review | None:
        stmt = select(Review).where(Review.booking_id == booking_id)
        return session.execute(stmt).scalar_one_or_none()

    def list_by_field(self, session: Session, field_id: int) -> list[Review]:
        stmt = select(Review).where(Review.field_id == field_id).order_by(Review.created_at.desc())
        return list(session.execute(stmt).scalars().all())

    def add(self, session: Session, review: Review) -> Review:
        session.add(review)
        session.flush()
        return review
