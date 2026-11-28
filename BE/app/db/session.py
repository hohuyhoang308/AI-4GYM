from collections.abc import Generator
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import create_engine, delete, inspect, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


logger = logging.getLogger(__name__)

# Bản ghi chống gửi lặp (request_id) chỉ cần giữ trong thời gian người dùng có thể bấm gửi lại.
CHAT_REQUEST_RETENTION = timedelta(hours=24)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


database_url = URL.create(
    "mysql+pymysql",
    username=settings.database_user,
    password=settings.database_password,
    host=settings.database_host,
    port=settings.database_port,
    database=settings.database_name,
    query={"charset": "utf8mb4"},
)
engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


# Các cột thời gian cần nâng lên DATETIME(6) với database đã tạo bằng phiên bản cũ.
_DATETIME_COLUMNS = {
    "users": ("created_at",),
    "login_sessions": ("created_at", "expires_at"),
    "conversations": ("created_at", "updated_at"),
    "chat_messages": ("created_at",),
    "chat_request_records": ("created_at",),
}


def upgrade_datetime_precision(bind: Engine) -> list[str]:
    """Nâng cột DATETIME(0) cũ lên DATETIME(6) trên MySQL; trả về danh sách cột đã đổi."""
    if bind.dialect.name != "mysql":
        return []
    changed = []
    with bind.begin() as connection:
        rows = connection.execute(text(
            "SELECT TABLE_NAME, COLUMN_NAME, DATETIME_PRECISION FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND DATA_TYPE = 'datetime'"
        )).all()
        for table, column, precision in rows:
            if column in _DATETIME_COLUMNS.get(table, ()) and (precision or 0) < 6:
                connection.execute(text(f"ALTER TABLE `{table}` MODIFY `{column}` DATETIME(6) NOT NULL"))
                changed.append(f"{table}.{column}")
    if changed:
        logger.info("Đã nâng độ chính xác thời gian: %s", ", ".join(changed))
    return changed


def purge_stale_records(db: Session) -> None:
    """Dọn phiên đăng nhập hết hạn và bản ghi request_id quá hạn lưu giữ."""
    from app.db.models import ChatRequestRecord, LoginSession

    now = utc_now()
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
    db.execute(delete(ChatRequestRecord).where(ChatRequestRecord.created_at < now - CHAT_REQUEST_RETENTION))
    db.commit()


def init_schema(bind: Engine | None = None) -> None:
    from app.db import models  # noqa: F401  # register ORM tables

    bind = bind or engine
    Base.metadata.create_all(bind=bind)
    if inspect(bind).has_table("chat_messages"):
        upgrade_datetime_precision(bind)
    with Session(bind) as db:
        purge_stale_records(db)
