from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FacilityStatus


class Facility(Base):
    """Cơ sở sân (địa điểm kinh doanh) do một Chủ sân đăng ký; có thể có nhiều Sân.
    Phải được Quản trị viên duyệt (UC24) trước khi hiển thị công khai cho khách tìm kiếm."""

    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    area: Mapped[str] = mapped_column(String(100), nullable=False)  # khu vực/quận
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancellation_policy: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[FacilityStatus] = mapped_column(
        Enum(FacilityStatus), nullable=False, default=FacilityStatus.PENDING
    )
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="facilities", foreign_keys=[owner_id])
    staff = relationship("User", back_populates="employer_facility", foreign_keys="User.facility_id")
    fields = relationship("Field", back_populates="facility", cascade="all, delete-orphan")
