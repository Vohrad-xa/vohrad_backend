import sqlalchemy as sa
from database import Base
from sqlalchemy.sql import func
from uuid import uuid4

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (
        sa.Index("idx_tenants_sub_domain", "sub_domain", unique=True),
        sa.Index("idx_tenants_tenant_schema_name", "tenant_schema_name", unique=True),
        sa.Index("idx_tenants_status", "status"),
        sa.Index("idx_tenants_email", "email"),
        sa.Index("idx_tenants_created_at", "created_at"),
        sa.Index("idx_tenants_created_by", "created_by"),
        sa.Index("idx_tenants_deleted_at", "deleted_at"),
        sa.Index("idx_tenants_status_deleted", "status", "deleted_at"),
        {"schema": "shared", "extend_existing": True},
    )

    tenant_id = sa.Column(
        "tenant_id",
        sa.UUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="The unique identifier for the tenant",
    )

    tenant_schema_name = sa.Column(
        "tenant_schema_name",
        sa.String(256),
        nullable=False,
        unique=True,
        comment="The schema for the database of the tenant example: site1",
    )

    sub_domain = sa.Column(
        "sub_domain",
        sa.String(256),
        nullable=False,
        index=True,
        unique=True,
        comment="the name of the tenant example: site1",
    )

    email = sa.Column(sa.String, nullable=True)
    telephone = sa.Column(sa.String, nullable=True)
    street = sa.Column(sa.String, nullable=True)
    street_number = sa.Column(sa.String, nullable=True)
    city = sa.Column(sa.String, nullable=True)
    province = sa.Column(sa.String, nullable=True)
    postal_code = sa.Column(sa.String, nullable=True)
    remarks = sa.Column(sa.Text, nullable=True)
    website = sa.Column(sa.String, nullable=True)
    logo = sa.Column(sa.String, nullable=True)
    industry = sa.Column(sa.String, nullable=True)
    tax_id = sa.Column(sa.String, nullable=True)
    billing_address = sa.Column(sa.String, nullable=True)
    country = sa.Column(sa.String, nullable=True)
    timezone = sa.Column(sa.String, nullable=True)
    status = sa.Column(sa.String, nullable=False, server_default="active")
    settings = sa.Column(sa.JSON, nullable=True)
    created_by = sa.Column(sa.UUID, nullable=True)
    created_at = sa.Column(sa.DateTime, nullable=False, server_default=func.now())
    updated_at = sa.Column(sa.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = sa.Column(sa.DateTime, nullable=True)
