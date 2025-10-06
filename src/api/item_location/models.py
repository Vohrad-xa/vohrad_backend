"""ItemLocation model (tenant schemas)."""

from database import Base
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4


class ItemLocation(Base):
    """Junction table linking items to locations with quantity tracking."""

    __tablename__ = "item_locations"
    __table_args__ = (
        sa.Index("idx_item_locations_item_id", "item_id"),
        sa.Index("idx_item_locations_location_id", "location_id"),
        sa.Index("idx_item_locations_moved_date", "moved_date"),
        sa.UniqueConstraint("item_id", "location_id", name="uq_item_location"),
        sa.CheckConstraint("quantity >= 1", name="ck_item_location_quantity_positive"),
    )

    id          = sa.Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    item_id     = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    location_id = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    quantity    = sa.Column(sa.Numeric(10, 2), nullable=False, server_default=sa.text('1'))
    moved_date  = sa.Column(sa.Date, nullable=True)
    notes       = sa.Column(sa.Text, nullable=True)
    created_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at  = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    item        = relationship("Item", back_populates="item_locations", lazy="selectin")
    location    = relationship("Location", back_populates="item_locations", lazy="selectin")
