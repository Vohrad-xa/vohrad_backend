"""License model (shared schema)."""

from database import Base
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from uuid import uuid4


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (
        sa.Index("idx_licenses_tenant_id", "tenant_id"),
        sa.Index("idx_licenses_license_key", "license_key", unique=True),
        sa.Index("idx_licenses_status", "status"),
        sa.Index("idx_licenses_starts_at", "starts_at"),
        sa.Index("idx_licenses_ends_at", "ends_at"),
        {"schema": "shared", "extend_existing": True},
    )

    id          = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    tenant_id   = sa.Column(sa.UUID, sa.ForeignKey("shared.tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    name        = sa.Column(sa.String(256), nullable=False)
    price       = sa.Column(sa.Numeric(10, 2), nullable=False, server_default="0")
    seats       = sa.Column(sa.Integer, nullable=False, server_default="1")
    license_key = sa.Column(sa.String(256), nullable=False, unique=True)
    starts_at   = sa.Column(sa.DateTime(timezone=True), nullable=False)
    ends_at     = sa.Column(sa.DateTime(timezone=True), nullable=True)
    status      = sa.Column(sa.String(50), nullable=False, server_default="inactive")
    features    = sa.Column(JSONB, nullable=True)
    meta        = sa.Column(JSONB, nullable=True)
    created_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
