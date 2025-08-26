import sqlalchemy as sa
from database import Base
from sqlalchemy.sql import func
from uuid import uuid4

class Admin(Base):
    """Platform administrators in shared schema"""
    __tablename__ = "admins"
    __table_args__ = (
        {"schema": "shared", "extend_existing": True},
        sa.Index("idx_admins_email", "email", unique=True),
        sa.Index("idx_admins_role", "role"),
        sa.Index("idx_admins_is_active", "is_active"),
        sa.Index("idx_admins_role_active", "role", "is_active"),
        sa.CheckConstraint("role IN ('super_admin', 'admin', 'support')", name="check_global_user_role"),
    )

    id = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    email = sa.Column(sa.String, nullable=False, unique=True)
    password = sa.Column(sa.String, nullable=False)
    first_name = sa.Column(sa.String(50), nullable=True)
    last_name = sa.Column(sa.String(50), nullable=True)
    role = sa.Column(sa.String(20), nullable=False)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
