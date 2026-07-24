import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    FIELD_OWNER = "FIELD_OWNER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class SportType(str, enum.Enum):
    FOOTBALL = "FOOTBALL"       # bóng đá mini
    BADMINTON = "BADMINTON"     # cầu lông
    TENNIS = "TENNIS"           # tennis


class FacilityStatus(str, enum.Enum):
    PENDING = "PENDING"         # chờ duyệt
    APPROVED = "APPROVED"       # đã duyệt, công khai
    REJECTED = "REJECTED"       # bị từ chối, trả lại cho chủ sân chỉnh sửa


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"                         # chờ thanh toán (giữ chỗ tạm thời)
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"  # đã nộp minh chứng, chờ nhân viên đối chiếu
    CONFIRMED = "CONFIRMED"                     # đã xác nhận, đã đặt cọc
    COMPLETED = "COMPLETED"                     # đã sử dụng sân xong
    CANCELLED = "CANCELLED"                     # khách hủy
    EXPIRED = "EXPIRED"                         # quá thời gian giữ chỗ mà chưa thanh toán

    # Các status được xem là "đang chiếm khung giờ" -> dùng cho unique index chống trùng lịch
    @classmethod
    def active_statuses(cls):
        return [cls.PENDING, cls.AWAITING_CONFIRMATION, cls.CONFIRMED, cls.COMPLETED]


class ComplaintStatus(str, enum.Enum):
    OPEN = "OPEN"                 # mới gửi, chưa xử lý
    IN_PROGRESS = "IN_PROGRESS"   # quản trị viên đang xử lý
    RESOLVED = "RESOLVED"         # đã giải quyết
    REJECTED = "REJECTED"         # từ chối (khiếu nại không hợp lệ)
