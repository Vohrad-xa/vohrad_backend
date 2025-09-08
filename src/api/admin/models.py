"""Admin model (shared schema)."""

from database import Base
import sqlalchemy as sa
from sqlalchemy.sql import func
from uuid import uuid4


class Admin(Base):
    """Platform administrators in shared schema"""

    __tablename__ = "users"
    __table_args__ = (
        sa.Index("idx_users_email", "email", unique=True),
        sa.Index("idx_users_role", "role"),
        sa.Index("idx_users_active", "is_active"),
        sa.CheckConstraint("role IN ('super_admin', 'admin')", name="check_global_user_role"),
        {"schema": "shared", "extend_existing": True},
    )

    id                 = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    email              = sa.Column(sa.String, nullable=False, unique=True)
    password           = sa.Column(sa.String, nullable=False)
    first_name         = sa.Column(sa.String(50), nullable=True)
    last_name          = sa.Column(sa.String(50), nullable=True)
    role               = sa.Column(sa.String(20), nullable=False)
    is_active          = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    email_verified_at  = sa.Column(sa.DateTime(timezone=True), nullable=True)
    date_of_birth      = sa.Column(sa.Date, nullable=True)
    address            = sa.Column(sa.Text, nullable=True)
    city               = sa.Column(sa.String, nullable=True)
    province           = sa.Column(sa.String, nullable=True)
    postal_code        = sa.Column(sa.String, nullable=True)
    country            = sa.Column(sa.String, nullable=True)
    phone_number       = sa.Column(sa.String(20), nullable=True)
    created_at         = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at         = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    tokens_valid_after = sa.Column(
        sa.DateTime(timezone=True), nullable=True, comment="All tokens issued before this timestamp are invalid"
    )

    @property
    def tenant_id(self):
        return None
