from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset import PasswordResetToken


class PasswordResetRepository:
    def add(self, session: Session, token: PasswordResetToken) -> PasswordResetToken:
        session.add(token)
        session.flush()
        return token

    def get_valid(self, session: Session, user_id: int, code: str) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.code == code,
                PasswordResetToken.used.is_(False),
            )
            .order_by(PasswordResetToken.created_at.desc())
        )
        return session.execute(stmt).scalars().first()
