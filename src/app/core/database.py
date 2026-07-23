"""Data access layer bootstrap: SQLAlchemy engine + session factory.

Đây là thành phần trung tâm của lớp Data Access trong kiến trúc 3 lớp.
Toàn bộ repositories bên trên dùng chung engine/session này.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

# check_same_thread=False vì NiceGUI phục vụ nhiều request/coroutine
# trên cùng process; mỗi thao tác vẫn mở/đóng session riêng (xem get_session()).
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


@contextmanager
def get_session():
    """Cung cấp một SQLAlchemy Session theo dạng context manager,
    tự commit khi thành công và rollback khi có lỗi (bao gồm cả lỗi
    vi phạm unique constraint khi 2 khách đặt trùng khung giờ)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Tạo toàn bộ bảng nếu chưa tồn tại. Gọi khi app khởi động / khi seed dữ liệu."""
    from app import models  # noqa: F401  (đảm bảo mọi model đã được import để đăng ký với Base.metadata)

    Base.metadata.create_all(bind=engine)
