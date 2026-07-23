"""Data Access layer cho Booking.

Lưu ý: repository này KHÔNG tự kiểm tra trùng lịch bằng SELECT trước khi INSERT
(cách làm đó có race-condition). Việc chống trùng lịch được đảm bảo bởi partial
unique index khai báo trong app.models.booking.Booking (xem docstring ở đó) và
được xử lý (bắt IntegrityError) ở tầng service - app.services.booking_service.
"""
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus


class BookingRepository:
    def get_by_id(self, session: Session, booking_id: int) -> Booking | None:
        return session.get(Booking, booking_id)

    def add(self, session: Session, booking: Booking) -> Booking:
        session.add(booking)
        session.flush()  # flush để DB kiểm tra unique index ngay, ném IntegrityError nếu trùng
        return booking

    def list_by_customer(self, session: Session, customer_id: int) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.customer_id == customer_id)
            .order_by(Booking.booking_date.desc(), Booking.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())

    def list_booked_slot_ids(self, session: Session, field_id: int, on_date: date) -> set[int]:
        """Trả về tập time_slot_id đang bị chiếm (PENDING/CONFIRMED/COMPLETED) của 1 sân trong 1 ngày.
        Dùng để hiển thị khung giờ trống khi tìm kiếm (UC002) - đây chỉ là gợi ý cho UI,
        ràng buộc đúng đắn cuối cùng vẫn nằm ở unique index khi thực sự tạo booking."""
        stmt = select(Booking.time_slot_id).where(
            Booking.field_id == field_id,
            Booking.booking_date == on_date,
            Booking.status.in_(BookingStatus.active_statuses()),
        )
        return set(session.execute(stmt).scalars().all())

    def list_expired_pending(self, session: Session, now: datetime) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.status == BookingStatus.PENDING,
            Booking.hold_expires_at < now,
        )
        return list(session.execute(stmt).scalars().all())

    def revenue_by_owner(self, session: Session, owner_id: int) -> list[tuple]:
        """Tổng doanh thu (deposit đã thu) theo từng sân của 1 chủ sân,
        chỉ tính các booking đã CONFIRMED hoặc COMPLETED (đã đặt cọc thật)."""
        from app.models.field import Field

        stmt = (
            select(Field.name, func.count(Booking.id), func.sum(Booking.deposit_amount))
            .join(Booking, Booking.field_id == Field.id)
            .where(
                Field.owner_id == owner_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
            )
            .group_by(Field.name)
        )
        return list(session.execute(stmt).all())
