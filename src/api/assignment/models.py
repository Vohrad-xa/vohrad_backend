"""Role assignment model."""

from database import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Assignment(Base):
    """Schema is determined by SQLAlchemy's schema translation at runtime."""

    __tablename__ = "assignments"
    __table_args__ = (
        sa.Index("idx_assignments_user_id", "user_id"),
        sa.Index("idx_assignments_role_id", "role_id"),
        sa.Index("idx_assignments_assigned_by", "assigned_by"),
    )

    user_id = sa.Column(sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    role_id = sa.Column(sa.UUID, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    assigned_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = sa.Column(sa.UUID, nullable=True)

    user = relationship("User", back_populates="assignments")
    role = relationship("Role", back_populates="assignments")
