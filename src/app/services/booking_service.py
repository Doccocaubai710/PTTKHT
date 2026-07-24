"""Business logic cho UC08 (đặt sân), UC09 (đặt cọc), UC10 (hủy), UC11 (đổi lịch),
UC18 (xác nhận thanh toán), UC19 (check-in), UC20 (đặt hộ khách vãng lai),
UC21 (xử lý đổi/hủy tại chỗ) + state machine của Booking.
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
    BookingStatus.PENDING: {
        BookingStatus.AWAITING_CONFIRMATION,
        BookingStatus.CONFIRMED,  # nhân viên xác nhận tiền mặt tại quầy (walk-in)
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
    },
    BookingStatus.AWAITING_CONFIRMATION: {
        BookingStatus.CONFIRMED,
        BookingStatus.PENDING,  # nhân viên từ chối minh chứng, yêu cầu bổ sung lại
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
    },
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

    # ---- UC08 (+ UC20 khi created_by_id != customer_id, tức nhân viên đặt hộ) ----
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

    # ---- UC09: khách tải lên minh chứng chuyển khoản (QR/chuyển khoản) ----
    def submit_payment_proof(self, booking_id: int, customer_id: int, proof_ref: str) -> Booking:
        if not proof_ref:
            raise BookingError("Vui lòng nhập mã giao dịch / minh chứng chuyển khoản.")

        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")
            if booking.customer_id != customer_id:
                raise BookingError("Bạn không có quyền thao tác trên đặt sân này.")

            self._auto_expire_if_overdue(booking)
            validate_transition(booking.status, BookingStatus.AWAITING_CONFIRMATION)

            booking.payment_method = "ONLINE_QR"
            booking.payment_proof_ref = proof_ref
            booking.payment_rejected_reason = None
            booking.status = BookingStatus.AWAITING_CONFIRMATION

            session.flush()
            session.expunge(booking)
            return booking

    # ---- UC18: nhân viên đối chiếu & xác nhận giao dịch chuyển khoản ----
    def confirm_payment(self, booking_id: int, staff_id: int) -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            validate_transition(booking.status, BookingStatus.CONFIRMED)

            booking.is_deposit_paid = True
            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_by_id = staff_id

            session.flush()
            session.expunge(booking)
            return booking

    # ---- UC18 (luồng thay thế): không khớp minh chứng -> từ chối, yêu cầu bổ sung ----
    def reject_payment(self, booking_id: int, staff_id: int, reason: str) -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            validate_transition(booking.status, BookingStatus.PENDING)

            booking.status = BookingStatus.PENDING
            booking.payment_rejected_reason = reason
            booking.confirmed_by_id = staff_id
            # cho khách thêm thời gian để bổ sung minh chứng đúng
            booking.hold_expires_at = datetime.utcnow() + timedelta(minutes=BOOKING_HOLD_MINUTES)

            session.flush()
            session.expunge(booking)
            return booking

    # ---- UC18 / UC20: nhân viên xác nhận thu tiền mặt tại quầy (walk-in) ----
    def confirm_cash_payment(self, booking_id: int, staff_id: int) -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            validate_transition(booking.status, BookingStatus.CONFIRMED)

            booking.is_deposit_paid = True
            booking.payment_method = "CASH"
            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_by_id = staff_id

            session.flush()
            session.expunge(booking)
            return booking

    # ---- UC10 / UC21: hủy đặt sân (áp dụng chính sách hoàn cọc theo thời gian hủy) ----
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
            # PENDING/AWAITING_CONFIRMATION -> CANCELLED: chưa xác nhận nên không có gì để hoàn

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.utcnow()
            booking.cancel_reason = reason
            booking.refund_amount = refund

            session.flush()
            return CancelResult(booking_id=booking.id, refund_amount=refund, new_status=booking.status)

    # ---- UC11 / UC21: đổi lịch đặt sân sang khung giờ/sân/ngày khác ----
    def reschedule_booking(
        self,
        booking_id: int,
        new_field_id: int,
        new_time_slot_id: int,
        new_booking_date: date,
    ) -> Booking:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise BookingError("Không tìm thấy đặt sân.")

            if booking.status not in (BookingStatus.PENDING, BookingStatus.AWAITING_CONFIRMATION, BookingStatus.CONFIRMED):
                raise BookingError("Chỉ có thể đổi lịch cho đặt sân đang chờ xử lý hoặc đã xác nhận.")

            if new_booking_date < date.today():
                raise BookingError("Không thể đổi sang một ngày đã qua.")

            if booking.status == BookingStatus.CONFIRMED:
                hours_until_play = self._hours_until_play(booking)
                if hours_until_play < CANCEL_PARTIAL_REFUND_HOURS:
                    raise BookingError(
                        f"Không thể đổi lịch khi còn dưới {CANCEL_PARTIAL_REFUND_HOURS} giờ nữa đến giờ chơi."
                    )

            new_slot = self.slot_repo.get_by_id(session, new_time_slot_id)
            if not new_slot or new_slot.field_id != new_field_id or not new_slot.is_active:
                raise BookingError("Khung giờ mới không hợp lệ hoặc đã ngừng hoạt động.")

            booking.field_id = new_field_id
            booking.time_slot_id = new_time_slot_id
            booking.booking_date = new_booking_date
            booking.total_price = new_slot.price
            booking.deposit_amount = round(new_slot.price * DEPOSIT_RATIO, -3) or new_slot.price
            booking.reschedule_count += 1

            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                raise BookingError("Khung giờ mới đã có người đặt, vui lòng chọn khung giờ khác.")

            session.expunge(booking)
            return booking

    # ---- UC19: nhân viên check-in khách & xác nhận hoàn tất sử dụng sân ----
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

    # ---- Job định kỳ: chuyển các booking PENDING/AWAITING_CONFIRMATION quá hạn sang EXPIRED ----
    def expire_overdue_bookings(self) -> int:
        with get_session() as session:
            now = datetime.utcnow()
            overdue = self.booking_repo.list_expired_pending(session, now)
            for booking in overdue:
                self._expire(booking)
            return len(overdue)

    def _auto_expire_if_overdue(self, booking: Booking) -> None:
        if booking.status in (BookingStatus.PENDING, BookingStatus.AWAITING_CONFIRMATION) and (
            datetime.utcnow() > booking.hold_expires_at
        ):
            self._expire(booking)
            raise BookingError("Đã quá thời gian giữ chỗ, vui lòng đặt lại khung giờ khác.")

    def _expire(self, booking: Booking) -> None:
        if booking.status in (BookingStatus.PENDING, BookingStatus.AWAITING_CONFIRMATION):
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

    def list_facility_bookings(self, facility_id: int, on_date: date | None = None) -> list[Booking]:
        with get_session() as session:
            bookings = self.booking_repo.list_by_facility(session, facility_id, on_date)
            session.expunge_all()
            return bookings

    def get_booking(self, booking_id: int) -> Booking | None:
        with get_session() as session:
            booking = self.booking_repo.get_by_id(session, booking_id)
            if booking:
                session.expunge(booking)
            return booking

    # ---- Chủ sân: báo cáo doanh thu (UC17) ----
    def revenue_report(self, owner_id: int) -> list[tuple]:
        with get_session() as session:
            return self.booking_repo.revenue_by_owner(session, owner_id)

    # ---- Quản trị viên: thống kê toàn hệ thống (UC26) ----
    def system_stats(self) -> dict:
        with get_session() as session:
            return self.booking_repo.system_stats(session)
