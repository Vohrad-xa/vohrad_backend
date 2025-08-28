import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all models in the application."""

    __abstract__ = True
    metadata = sa.MetaData(schema="tenant_default")
