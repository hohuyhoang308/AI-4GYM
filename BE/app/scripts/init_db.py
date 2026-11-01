import re

import pymysql

from app.core.config import settings
from app.db.session import init_schema


def main() -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", settings.database_name):
        raise ValueError("DATABASE_NAME chỉ được chứa chữ, số và dấu gạch dưới")
    connection = pymysql.connect(
        host=settings.database_host,
        port=settings.database_port,
        user=settings.database_user,
        password=settings.database_password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()
    init_schema()
    print(f"MySQL schema ready: {settings.database_name}")


if __name__ == "__main__":
    main()
