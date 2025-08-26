import sqlalchemy as sa
from database import Base
from sqlalchemy.sql import func
from uuid import uuid4

class Permission(Base):
    """Reusable permission model for both shared and tenant schemas"""
    __tablename__ = "permissions"
    __table_args__ = (
        sa.UniqueConstraint("role_id", "resource", "action"),
        sa.Index("idx_permissions_role_id", "role_id"),
        sa.Index("idx_permissions_resource", "resource"),
        sa.Index("idx_permissions_resource_action", "resource", "action"),
        sa.Index("idx_permissions_role_resource", "role_id", "resource"),
    )

    id = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    role_id = sa.Column(sa.UUID, sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource = sa.Column(sa.String(50), nullable=False)
    action = sa.Column(sa.String(50), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
