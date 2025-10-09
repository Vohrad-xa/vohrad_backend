"""Async SQLAlchemy engine configuration."""

from config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine

__all__ = ["async_engine"]

settings = get_settings()

# Convert sync database URL to async URL
ASYNC_SQLALCHEMY_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

if settings.is_development:
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        echo          = True,
        pool_size     = 75,
        max_overflow  = 75,
        pool_timeout  = 60,
        pool_recycle  = 3600,
        pool_pre_ping = True,
    )
else:
    async_engine = create_async_engine(
        ASYNC_SQLALCHEMY_DATABASE_URL,
        pool_size     = 70,
        max_overflow  = 70,
        pool_timeout  = 60,
        pool_recycle  = 3600,
        pool_pre_ping = True,
    )
