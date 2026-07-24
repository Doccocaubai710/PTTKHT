"""Business logic cho UC22 (viết đánh giá) và UC23 (chủ sân phản hồi đánh giá)."""
from datetime import datetime

from app.core.database import get_session
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.review import Review
from app.repositories.booking_repository import BookingRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.field_repository import FieldRepository
from app.repositories.review_repository import ReviewRepository


class ReviewError(Exception):
    pass


class ReviewService:
    def __init__(self):
        self.review_repo = ReviewRepository()
        self.booking_repo = BookingRepository()
        self.field_repo = FieldRepository()
        self.facility_repo = FacilityRepository()

    # ---- UC22: khách hàng đánh giá sau khi hoàn tất một Đặt sân ----
    def submit_review(self, booking_id: int, customer_id: int, rating: int, comment: str | None = None) -> Review:
        if rating < 1 or rating > 5:
            raise ReviewError("Đánh giá phải từ 1 đến 5 sao.")

        with get_session() as session:
            booking: Booking | None = self.booking_repo.get_by_id(session, booking_id)
            if not booking:
                raise ReviewError("Không tìm thấy đặt sân.")
            if booking.customer_id != customer_id:
                raise ReviewError("Bạn không có quyền đánh giá lượt đặt sân này.")
            if booking.status != BookingStatus.COMPLETED:
                raise ReviewError("Chỉ có thể đánh giá sau khi đã sử dụng sân xong.")
            if self.review_repo.get_by_booking(session, booking_id):
                raise ReviewError("Bạn đã đánh giá cho lượt đặt sân này rồi.")

            review = Review(
                booking_id=booking_id,
                field_id=booking.field_id,
                customer_id=customer_id,
                rating=rating,
                comment=comment,
            )
            self.review_repo.add(session, review)
            session.expunge(review)
            return review

    def list_field_reviews(self, field_id: int) -> list[Review]:
        with get_session() as session:
            reviews = self.review_repo.list_by_field(session, field_id)
            session.expunge_all()
            return reviews

    def list_owner_reviews(self, owner_id: int) -> list[Review]:
        with get_session() as session:
            reviews = self.review_repo.list_by_owner(session, owner_id)
            session.expunge_all()
            return reviews

    # ---- UC23: chủ sân xem và phản hồi đánh giá của khách hàng ----
    def reply_to_review(self, review_id: int, owner_id: int, reply: str) -> Review:
        if not reply:
            raise ReviewError("Vui lòng nhập nội dung phản hồi.")

        with get_session() as session:
            review = self.review_repo.get_by_id(session, review_id)
            if not review:
                raise ReviewError("Không tìm thấy đánh giá.")

            field = self.field_repo.get_by_id(session, review.field_id)
            facility = self.facility_repo.get_by_id(session, field.facility_id) if field else None
            if not facility or facility.owner_id != owner_id:
                raise ReviewError("Bạn không có quyền phản hồi đánh giá này.")

            review.owner_reply = reply
            review.replied_at = datetime.utcnow()

            session.flush()
            session.expunge(review)
            return review
