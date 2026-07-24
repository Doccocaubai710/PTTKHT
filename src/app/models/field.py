from datetime import datetime, time

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SportType


class Field(Base):
    """Một sân thể thao cụ thể (VD: Sân bóng mini A1), thuộc về một Cơ sở sân (Facility)."""

    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sport_type: Mapped[SportType] = mapped_column(Enum(SportType), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="fields")
    time_slots = relationship(
        "FieldTimeSlot", back_populates="field", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="field")
    reviews = relationship("Review", back_populates="field")


class FieldTimeSlot(Base):
    """Khung giờ & giá chuẩn (template) của một sân, ví dụ 06:00-07:00 giá 200.000đ.
    Chủ sân tạo/sửa/xóa các bản ghi này ở UC14/UC15. Khi khách đặt sân (UC08), họ chọn
    một FieldTimeSlot cho một ngày cụ thể -> tạo ra một Booking."""

    __tablename__ = "field_time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    field = relationship("Field", back_populates="time_slots")
    bookings = relationship("Booking", back_populates="time_slot")
