"""Business logic cho UC008 - Đánh giá sân sau khi sử dụng."""
from app.core.database import get_session
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.review import Review
from app.repositories.booking_repository import BookingRepository
from app.repositories.review_repository import ReviewRepository


class ReviewError(Exception):
    pass


class ReviewService:
    def __init__(self):
        self.review_repo = ReviewRepository()
        self.booking_repo = BookingRepository()

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
