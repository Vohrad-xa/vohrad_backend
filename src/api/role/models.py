import sqlalchemy as sa

# Import Assignment to ensure table is available for secondary relationship
from api.assignment.models import Assignment
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4


class Role(Base):
    """Reusable role model for both shared and tenant schemas"""
    __tablename__  = "roles"
    __table_args__ = (
        sa.Index("idx_roles_is_active", "is_active"),
        sa.Index("idx_roles_name", "name", unique=True),
        sa.Index("idx_roles_active_name", "is_active", "name"),
    )

    id          = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    name        = sa.Column(sa.String(50), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=True)
    is_active   = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    created_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())

    """ORM Relationships."""
    users = relationship(
        "User",
        secondary      = Assignment.__table__,
        back_populates = "roles",
        lazy           = "selectin"
    )
    permissions = relationship("Permission", back_populates="role", lazy="selectin")
