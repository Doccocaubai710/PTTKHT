from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Review(Base):
    """Đánh giá sân sau khi khách đã sử dụng (booking ở trạng thái COMPLETED)."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="review")
    field = relationship("Field", back_populates="reviews")
    customer = relationship("User", back_populates="reviews")
