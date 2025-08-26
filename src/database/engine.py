from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import get_settings

__all__ = ["async_engine"]

ASYNC_SQLALCHEMY_DATABASE_URL = (
    "postgresql+asyncpg://"
    + get_settings().DB_USER
    + ":"
    + get_settings().DB_PASS
    + "@"
    + get_settings().DB_HOST
    + ":"
    + get_settings().DB_PORT
    + "/"
    + get_settings().DB_NAME
)

if get_settings().ENVIRONMENT == "development":
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        echo=True,
        pool_size=75,
        max_overflow=75,
        pool_timeout=60,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
else:
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        pool_size=70,
        max_overflow=70,
        pool_timeout=60,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
