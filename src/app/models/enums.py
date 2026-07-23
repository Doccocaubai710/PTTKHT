import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    FIELD_OWNER = "FIELD_OWNER"
    STAFF = "STAFF"


class SportType(str, enum.Enum):
    FOOTBALL = "FOOTBALL"       # bóng đá mini
    BADMINTON = "BADMINTON"     # cầu lông
    TENNIS = "TENNIS"           # tennis


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"         # chờ thanh toán (giữ chỗ tạm thời)
    CONFIRMED = "CONFIRMED"     # đã xác nhận, đã đặt cọc
    COMPLETED = "COMPLETED"     # đã sử dụng sân xong
    CANCELLED = "CANCELLED"     # khách hủy
    EXPIRED = "EXPIRED"         # quá thời gian giữ chỗ mà chưa thanh toán

    # Các status được xem là "đang chiếm khung giờ" -> dùng cho unique index chống trùng lịch
    @classmethod
    def active_statuses(cls):
        return [cls.PENDING, cls.CONFIRMED, cls.COMPLETED]
