import sqlalchemy as sa
from database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from uuid import uuid4

class User(Base):
    """Business users in tenant schemas"""
    __tablename__ = "users"
    __table_args__ = (
        sa.Index("idx_users_tenant_id", "tenant_id"),
        sa.Index("idx_users_tenant_id_id", "tenant_id", "id"),
        sa.Index("idx_users_email", "email", unique=True),
        sa.Index("idx_users_email_verified", "email_verified_at"),
        sa.Index("idx_users_created_at", "created_at"),
    )

    id = sa.Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    tenant_id = sa.Column(
        PostgresUUID(as_uuid=True),
        sa.ForeignKey("shared.tenants.tenant_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    first_name = sa.Column(sa.String(50), nullable=True)
    last_name = sa.Column(sa.String(50), nullable=True)
    tenant_role = sa.Column(sa.String(32), nullable=True)
    email = sa.Column(sa.String, nullable=False, unique=True)
    email_verified_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    password = sa.Column(sa.String, nullable=False)
    date_of_birth = sa.Column(sa.Date, nullable=True)
    address = sa.Column(sa.Text, nullable=True)
    city = sa.Column(sa.String, nullable=True)
    province = sa.Column(sa.String, nullable=True)
    postal_code = sa.Column(sa.String, nullable=True)
    country = sa.Column(sa.String, nullable=True)
    phone_number = sa.Column(sa.String(20), nullable=True)
    remember_token = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
