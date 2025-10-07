"""Item model (tenant schemas)."""

from api.item_location.models import ItemLocation
from database import Base
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4


class Item(Base):
    """Items in tenant schemas with tracking modes."""

    __tablename__ = "items"
    __table_args__ = (
        sa.Index("idx_items_barcode", "barcode"),
        sa.Index("idx_items_tracking_mode", "tracking_mode"),
        sa.Index("idx_items_user_id", "user_id"),
        sa.Index("idx_items_parent_item_id", "parent_item_id"),
        sa.Index("idx_items_item_relation_id", "item_relation_id"),
        sa.Index("idx_items_is_active", "is_active"),
        sa.Index("idx_items_created_at", "created_at"),
        sa.UniqueConstraint("code", name="items_code_unique"),
        sa.UniqueConstraint("serial_number", name="items_serial_number_unique"),
    )
    TRACKING_ABSTRACT   = "abstract"
    TRACKING_STANDARD   = "standard"
    TRACKING_SERIALIZED = "serialized"

    id                     = sa.Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name                   = sa.Column(sa.String(100), nullable=False)
    code                   = sa.Column(sa.String(50), nullable=False)
    barcode                = sa.Column(sa.String, nullable=True)
    description            = sa.Column(sa.Text, nullable=True)
    tracking_mode          = sa.Column(sa.String(), nullable=False, default=TRACKING_ABSTRACT)
    price                  = sa.Column(sa.Numeric(10, 2), nullable=True)
    serial_number          = sa.Column(sa.String, nullable=True)
    notes                  = sa.Column(sa.Text, nullable=True)
    is_active              = sa.Column(sa.Boolean, nullable=False, default=True)
    specifications         = sa.Column(JSONB, nullable=True)
    tracking_changed_at    = sa.Column(sa.DateTime(timezone=True), nullable=True)
    tracking_change_reason = sa.Column(sa.Text, nullable=True)
    user_id                = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_item_id         = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    item_relation_id       = sa.Column(PostgresUUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    created_at             = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at             = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    parent                 = relationship("Item", remote_side="Item.id", foreign_keys=[parent_item_id], backref="children")
    item_locations         = relationship("ItemLocation", back_populates="item")
    related_item = relationship(
        "Item",
        remote_side  = "Item.id",
        foreign_keys = [item_relation_id],
        backref      = "item_relations"
    )
    locations = relationship(
        "Location",
        secondary = ItemLocation.__table__,
        viewonly  = True,
    )
