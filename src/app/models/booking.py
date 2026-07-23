from datetime import date, datetime

from sqlalchemy import DateTime, Date, Enum, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BookingStatus


class Booking(Base):
    """Một lượt đặt sân cho một FieldTimeSlot vào một ngày cụ thể.

    CHỐNG TRÙNG LỊCH: dùng một *partial unique index* trên tổ hợp
    (field_id, booking_date, time_slot_id) nhưng CHỈ áp dụng cho các bản ghi có
    status thuộc nhóm "đang chiếm chỗ" (PENDING, CONFIRMED, COMPLETED).

    Tại sao dùng unique index thay vì lock bi quan (SELECT ... FOR UPDATE) hay
    Redis distributed lock:
      - Đơn giản, không cần thêm hạ tầng (Redis) trong khi vẫn đảm bảo đúng
        100% tính đúng đắn nhờ chính DBMS (SQLite/Postgres) kiểm tra ràng buộc
        tại thời điểm COMMIT — không có khoảng hở race-condition nào giữa
        "kiểm tra" và "ghi" (check-then-act) như khi tự kiểm tra bằng SELECT
        trước rồi mới INSERT.
      - Không cần giữ lock xuyên suốt một transaction dài (pessimistic lock
        dễ gây nghẽn khi nhiều người dùng cùng tra cứu/đặt sân), trong khi
        lock bi quan yêu cầu transaction phải mở suốt quá trình thanh toán.
      - Vì đây là ứng dụng một instance (không phân tán nhiều service), không
        cần Redis lock vốn chỉ thật sự cần thiết khi có nhiều tiến trình/máy
        chủ độc lập tranh chấp cùng một tài nguyên.
      - Dùng partial index (chỉ áp dụng với status đang chiếm chỗ) để khi một
        booking chuyển sang CANCELLED/EXPIRED, khung giờ đó lại "nhả" ra cho
        người khác đặt mà không cần xoá lịch sử booking cũ.

    Luồng xử lý (xem BookingService.create_booking):
      1. Mở một transaction.
      2. INSERT booking mới với status=PENDING.
      3. Nếu vi phạm unique index -> DBMS raise IntegrityError ngay tại COMMIT.
      4. Service bắt IntegrityError, rollback, trả lỗi nghiệp vụ:
         "Khung giờ đã được đặt, vui lòng chọn khung giờ khác".
    """

    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "ux_booking_field_date_slot_active",
            "field_id",
            "booking_date",
            "time_slot_id",
            unique=True,
            sqlite_where=text("status IN ('PENDING', 'CONFIRMED', 'COMPLETED')"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False)
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("field_time_slots.id"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING
    )

    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_deposit_paid: Mapped[bool] = mapped_column(default=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # MOCK_ONLINE / CASH

    hold_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    refund_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    field = relationship("Field", back_populates="bookings")
    time_slot = relationship("FieldTimeSlot", back_populates="bookings")
    customer = relationship("User", back_populates="bookings_made", foreign_keys=[customer_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    review = relationship("Review", back_populates="booking", uselist=False)
