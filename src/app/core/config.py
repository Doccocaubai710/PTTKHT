"""Application-wide configuration constants."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'sportbook.db')}"

# JWT settings (demo only - in production this must come from a secret manager / env var)
JWT_SECRET = os.environ.get("SPORTBOOK_JWT_SECRET", "demo-secret-key-for-do-an-pttkht")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 8  # 8 hours

# NiceGUI browser storage secret (cookie signing for app.storage.user)
STORAGE_SECRET = os.environ.get("SPORTBOOK_STORAGE_SECRET", "demo-storage-secret")

# Business rules
BOOKING_HOLD_MINUTES = 10  # PENDING -> EXPIRED nếu quá thời gian này mà chưa thanh toán
CANCEL_FULL_REFUND_HOURS = 24  # hủy trước 24h thì hoàn 100% cọc
CANCEL_PARTIAL_REFUND_HOURS = 6  # hủy trước 6-24h thì hoàn 50% cọc, dưới 6h không hoàn
DEPOSIT_RATIO = 0.3  # đặt cọc 30% giá trị sân
