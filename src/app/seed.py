"""Seed dữ liệu mẫu: 2 cơ sở sân (1 đã duyệt, 1 chờ duyệt) với các sân/khung giờ,
5 tài khoản demo (customer/owner/staff/admin) và một vài dữ liệu minh họa khác.

Chạy: python -m app.seed  (từ thư mục src/, với conda env đã cài requirements)
"""
from datetime import time

from app.core.database import get_session, init_db
from app.core.security import hash_password
from app.models.enums import FacilityStatus, SportType, UserRole
from app.models.facility import Facility
from app.models.field import Field, FieldTimeSlot
from app.models.user import User
from app.repositories.facility_repository import FacilityRepository
from app.repositories.field_repository import FieldRepository, FieldTimeSlotRepository
from app.repositories.user_repository import UserRepository

DEMO_PASSWORD = "123456"


def run():
    init_db()
    user_repo = UserRepository()
    facility_repo = FacilityRepository()
    field_repo = FieldRepository()
    slot_repo = FieldTimeSlotRepository()

    with get_session() as session:
        if user_repo.get_by_phone(session, "0900000001"):
            print("Dữ liệu mẫu đã tồn tại, bỏ qua seed.")
            return

        owner = user_repo.add(
            session,
            User(
                full_name="Nguyễn Văn Chủ Sân",
                phone="0900000001",
                email="owner@demo.vn",
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.FIELD_OWNER,
            ),
        )
        customer = user_repo.add(
            session,
            User(
                full_name="Trần Thị Khách Hàng",
                phone="0900000002",
                email="customer@demo.vn",
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.CUSTOMER,
            ),
        )
        admin = user_repo.add(
            session,
            User(
                full_name="Phạm Thị Quản Trị",
                phone="0900000004",
                email="admin@demo.vn",
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.ADMIN,
            ),
        )

        facility1 = facility_repo.add(
            session,
            Facility(
                owner_id=owner.id,
                name="Khu liên hợp thể thao Thắng Lợi",
                area="Cầu Giấy",
                address="12 Xuân Thủy, Cầu Giấy, Hà Nội",
                description="Sân cỏ nhân tạo 5 người, có mái che.",
                cancellation_policy="Hủy trước 24h hoàn 100% cọc, trước 6h hoàn 50%, dưới 6h không hoàn cọc.",
                status=FacilityStatus.APPROVED,
                reviewed_by_id=admin.id,
            ),
        )
        facility2 = facility_repo.add(
            session,
            Facility(
                owner_id=owner.id,
                name="Cụm sân cầu lông - tennis Ánh Sáng",
                area="Thanh Xuân",
                address="45 Nguyễn Trãi, Thanh Xuân, Hà Nội",
                description="4 sân cầu lông sàn gỗ, 1 sân tennis mặt cứng, có đèn chiếu sáng ban đêm.",
                status=FacilityStatus.PENDING,  # minh họa UC24: đang chờ quản trị viên duyệt
            ),
        )

        staff = user_repo.add(
            session,
            User(
                full_name="Lê Văn Nhân Viên",
                phone="0900000003",
                email="staff@demo.vn",
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.STAFF,
                facility_id=facility1.id,
            ),
        )

        f1 = field_repo.add(
            session,
            Field(
                facility_id=facility1.id,
                name="Sân bóng đá mini A1",
                sport_type=SportType.FOOTBALL,
                description="Sân số 1, cỏ nhân tạo.",
            ),
        )
        f2 = field_repo.add(
            session,
            Field(
                facility_id=facility2.id,
                name="Sân cầu lông số 1",
                sport_type=SportType.BADMINTON,
                description="4 sân đơn, sàn gỗ, ánh sáng tốt.",
            ),
        )
        f3 = field_repo.add(
            session,
            Field(
                facility_id=facility2.id,
                name="Sân tennis số 1",
                sport_type=SportType.TENNIS,
                description="Mặt sân cứng, có đèn chiếu sáng ban đêm.",
            ),
        )

        for f, price_base in [(f1, 300000), (f2, 100000), (f3, 200000)]:
            for start_h, end_h in [(6, 7), (7, 8), (18, 19), (19, 20), (20, 21)]:
                slot_repo.add(
                    session,
                    FieldTimeSlot(
                        field_id=f.id,
                        start_time=time(start_h, 0),
                        end_time=time(end_h, 0),
                        price=price_base,
                    ),
                )

        print("Seed dữ liệu mẫu thành công.")
        print(f"  Chủ sân      : 0900000001 / {DEMO_PASSWORD}")
        print(f"  Khách        : 0900000002 / {DEMO_PASSWORD}")
        print(f"  Nhân viên    : 0900000003 / {DEMO_PASSWORD}")
        print(f"  Quản trị viên: 0900000004 / {DEMO_PASSWORD}")


if __name__ == "__main__":
    run()
