"""Password hashing (bcrypt) and JWT encode/decode helpers.

Ghi chú: hệ thống dùng NiceGUI (server-rendered UI qua websocket) nên không có
một "trình duyệt SPA" gọi REST API độc lập như kiến trúc React thông thường.
Tuy nhiên để vẫn minh họa đúng cơ chế xác thực JWT + phân quyền theo role như
yêu cầu đồ án, AuthService vẫn phát hành JWT thật sự khi đăng nhập; token này
được lưu trong app.storage.user (phiên làm việc phía server, gắn với browser
qua cookie đã ký) và được giải mã/kiểm tra lại ở mỗi trang được bảo vệ
(xem app/pages/guards.py) giống hệt cách một API backend thực thụ sẽ làm.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Trả về payload nếu token hợp lệ & còn hạn, ngược lại trả None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
