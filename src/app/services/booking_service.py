"""Business logic cho UC003 (đặt sân), UC004 (đặt cọc), UC005 (hủy đặt sân)
và UC007 (nhân viên đặt hộ khách walk-in) + state machine của Booking.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.core.config import (
    BOOKING_HOLD_MINUTES,
    CANCEL_FULL_REFUND_HOURS,
    CANCEL_PARTIAL_REFUND_HOURS,
    DEPOSIT_RATIO,
)
from app.core.database import get_session
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.repositories.booking_repository import BookingRepository
from app.repositories.field_repository import FieldTimeSlotRepository


class BookingError(Exception):
    """Lỗi nghiệp vụ, bao gồm cả trường hợp trùng lịch (thông báo thân thiện cho người dùng)."""


# ---------------------------------------------------------------------------
# STATE MACHINE: khai báo tường minh các transition hợp lệ (mục 3.2 đề bài).
# Bất kỳ chuyển trạng thái nào không có trong bảng này đều bị từ chối.
# ---------------------------------------------------------------------------
ALLOWED_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.EXPIRED: set(),
}


def validate_transition(current: BookingStatus, target: BookingStatus) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise BookingError(
            f"Không thể chuyển trạng thái đặt sân từ {current.value} sang {target.value}."
        )


@dataclass
class CancelResult:
    booking_id: int
    refund_amount: float
    new_status: BookingStatus


class BookingService:
    def __init__(self):
        self.booking_repo = BookingRepository()
        self.slot_repo = FieldTimeSlotRepository()

    # ---- UC003 (+ UC007 khi created_by_id != customer_id, tức nhân viên đặt hộ) ----
    def create_booking(
        self,
        field_id: int,
        time_slot_id: int,
        booking_date: date,
        customer_id: int,
        created_by_id: int,
    ) -> Booking:
        if booking_date < date.today():
            raise BookingError("Không thể đặt sân cho một ngày đã qua.")

        with get_session() as session:
            slot = self.slot_repo.get_by_id(session, time_slot_id)
            if not slot or slot.field_id != field_id or not slot.is_active:
                raise BookingError("Khung giờ không hợp lệ hoặc đã ngừng hoạt động.")

            total_price = slot.price
            deposit = round(total_price * DEPOSIT_RATIO, -3) or total_price  # làm tròn nghìn đồng

            booking = Booking(
                field_id=field_id,
                time_slot_id=time_slot_id,
                booking_date=booking_date,
                customer_id=customer_id,
                created_by_id=created_by_id,
                status=BookingStatus.PENDING,
                total_price=total_price,
                deposit_amount=deposit,
                hold_expires_at=datetime.utcnow() + timedelta(minutes=BOOKING_HOLD_MINUTES),
            )

            try:
                # INSERT + flush: đây là điểm DBMS kiểm tra partial unique index.
                # Không SELECT-kiểm-tra-trước để tránh race condition khi 2 khách
                # bấm đặt cùng lúc; thay vào đó ta để DB tự phát hiện xung đột
                # tại thời điểm ghi, rồi bắt lỗi bên dưới.
                self.booking_repo.add(session, booking)
            except IntegrityError:
                session.rollback()
                raise BookingError("Khung giờ đã được đặt, vui lòng chọn khung giờ khác.")

            session.expunge(booking)
            return booking

    # ---- UC004: thanh toán đặt cọc (mock, không tích hợp cổng thanh toán thật) ----
    def pay_deposit(self, booking_id: int, payment_method: str = "MOCK_ONLINE") -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            if booking.status == BookingStatus.EXPIRED or (
                booking.status == BookingStatus.PENDING and datetime.utcnow() > booking.hold_expires_at
            ):
                self._expire(booking)
                session.flush()
                raise BookingError("Đã quá thời gian giữ chỗ, vui lòng đặt lại khung giờ khác.")

            validate_transition(booking.status, BookingStatus.CONFIRMED)

            # MOCK: giả lập luôn thanh toán thành công (không gọi cổng thanh toán thật)
            booking.is_deposit_paid = True
            booking.payment_method = payment_method
            booking.status = BookingStatus.CONFIRMED

            session.flush()
            session.expunge(booking)
            return booking

    # ---- UC005: hủy đặt sân (áp dụng chính sách hoàn cọc theo thời gian hủy) ----
    def cancel_booking(self, booking_id: int, reason: str | None = None) -> CancelResult:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            validate_transition(booking.status, BookingStatus.CANCELLED)

            refund = 0.0
            if booking.status == BookingStatus.CONFIRMED:
                hours_until_play = self._hours_until_play(booking)
                if hours_until_play >= CANCEL_FULL_REFUND_HOURS:
                    refund = booking.deposit_amount  # hoàn 100%
                elif hours_until_play >= CANCEL_PARTIAL_REFUND_HOURS:
                    refund = round(booking.deposit_amount * 0.5, -3)  # hoàn 50%
                else:
                    refund = 0.0  # hủy sát giờ, không hoàn cọc
            # PENDING -> CANCELLED: chưa thanh toán nên không có gì để hoàn

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.utcnow()
            booking.cancel_reason = reason
            booking.refund_amount = refund

            session.flush()
            return CancelResult(booking_id=booking.id, refund_amount=refund, new_status=booking.status)

    # ---- Nhân viên xác nhận khách đã check-in / hoàn tất sử dụng sân ----
    def check_in_and_complete(self, booking_id: int) -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")
            validate_transition(booking.status, BookingStatus.COMPLETED)
            booking.status = BookingStatus.COMPLETED
            session.flush()
            session.expunge(booking)
            return booking

    # ---- Nhân viên xác nhận thanh toán tiền mặt tại quầy (walk-in, UC007) ----
    def confirm_cash_payment(self, booking_id: int) -> Booking:
        return self.pay_deposit(booking_id, payment_method="CASH")

    # ---- Job định kỳ: chuyển các booking PENDING quá hạn giữ chỗ sang EXPIRED ----
    def expire_overdue_bookings(self) -> int:
        with get_session() as session:
            now = datetime.utcnow()
            overdue = self.booking_repo.list_expired_pending(session, now)
            for booking in overdue:
                self._expire(booking)
            return len(overdue)

    def _expire(self, booking: Booking) -> None:
        if booking.status == BookingStatus.PENDING:
            validate_transition(booking.status, BookingStatus.EXPIRED)
            booking.status = BookingStatus.EXPIRED

    def _hours_until_play(self, booking: Booking) -> float:
        with get_session() as session:
            slot = self.slot_repo.get_by_id(session, booking.time_slot_id)
            play_start = datetime.combine(booking.booking_date, slot.start_time)
            return (play_start - datetime.utcnow()).total_seconds() / 3600

    def list_customer_bookings(self, customer_id: int) -> list[Booking]:
        with get_session() as session:
            bookings = self.booking_repo.list_by_customer(session, customer_id)
            session.expunge_all()
            return bookings

    def get_booking(self, booking_id: int) -> Booking | None:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if booking:
                session.expunge(booking)
            return booking

    # ---- Chủ sân: báo cáo doanh thu ----
    def revenue_report(self, owner_id: int) -> list[tuple]:
        with get_session() as session:
            return self.booking_repo.revenue_by_owner(session, owner_id)
