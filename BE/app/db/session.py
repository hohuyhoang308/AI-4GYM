from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


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


def init_schema() -> None:
    from app.db import models  # noqa: F401  # register ORM tables

    Base.metadata.create_all(bind=engine)
