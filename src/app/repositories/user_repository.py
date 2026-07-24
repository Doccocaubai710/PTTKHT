"""Data Access layer cho User. Không chứa business rule, chỉ truy vấn CRUD thuần."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, session: Session, user_id: int) -> User | None:
        return session.get(User, user_id)

    def get_by_phone(self, session: Session, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        return session.execute(stmt).scalar_one_or_none()

    def get_by_email(self, session: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return session.execute(stmt).scalar_one_or_none()

    def list_by_role(self, session: Session, role) -> list[User]:
        stmt = select(User).where(User.role == role)
        return list(session.execute(stmt).scalars().all())

    def list_by_facility(self, session: Session, facility_id: int) -> list[User]:
        stmt = select(User).where(User.facility_id == facility_id)
        return list(session.execute(stmt).scalars().all())

    def list_all(self, session: Session) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        return list(session.execute(stmt).scalars().all())

    def add(self, session: Session, user: User) -> User:
        session.add(user)
        session.flush()  # để lấy được user.id ngay mà chưa cần commit
        return user
