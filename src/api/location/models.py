"""Location model (tenant schemas)."""

from database import Base
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4


class Location(Base):
    """Locations in tenant schemas for hierarchical organization of physical spaces."""

    __tablename__ = "locations"
    __table_args__ = (
        sa.Index("idx_locations_parent_id", "parent_id"),
        sa.Index("idx_locations_is_active", "is_active"),
        sa.Index("idx_locations_path", "path"),
        sa.UniqueConstraint("code", name="locations_code_unique"),
    )

    id             = sa.Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name           = sa.Column(sa.String(255), nullable=False)
    code           = sa.Column(sa.String(50), nullable=False)
    parent_id      = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    path           = sa.Column(sa.String(500), nullable=True)
    description    = sa.Column(sa.Text, nullable=True)
    is_active      = sa.Column(sa.Boolean, nullable=False, default=True)
    created_at     = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at     = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    parent         = relationship("Location", remote_side="Location.id", foreign_keys=[parent_id], backref="children")
    item_locations = relationship("ItemLocation", back_populates="location")
