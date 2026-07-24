from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Chỉ áp dụng cho STAFF: cơ sở sân mà nhân viên này thuộc về (do Chủ sân tạo/gán - UC16).
    facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    facilities = relationship(
        "Facility", back_populates="owner", foreign_keys="Facility.owner_id"
    )
    employer_facility = relationship(
        "Facility", back_populates="staff", foreign_keys=[facility_id]
    )
    bookings_made = relationship(
        "Booking", back_populates="customer", foreign_keys="Booking.customer_id"
    )
    reviews = relationship("Review", back_populates="customer")
