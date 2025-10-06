"""create item_locations table

Revision ID: 64abac85073e
Revises: 51e8c0f63cd7
Create Date: 2025-10-05 02:37:41.981855

"""
from alembic import op
from migrations.tenant import for_each_tenant_schema
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '64abac85073e'
down_revision: Union[str, None] = '51e8c0f63cd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@for_each_tenant_schema
def upgrade(schema: str) -> None:
    op.create_table(
        "item_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("1")),
        sa.Column("moved_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["item_id"], [f"{schema}.items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], [f"{schema}.locations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("item_id", "location_id", name="uq_item_location"),
        sa.CheckConstraint("quantity >= 1", name="ck_item_location_quantity_positive"),
        schema=schema,
    )

    op.create_index("idx_item_locations_item_id", "item_locations", ["item_id"], schema=schema)
    op.create_index("idx_item_locations_location_id", "item_locations", ["location_id"], schema=schema)
    op.create_index("idx_item_locations_moved_date", "item_locations", ["moved_date"], schema=schema)


@for_each_tenant_schema
def downgrade(schema: str) -> None:
    op.drop_index("idx_item_locations_moved_date", table_name="item_locations", schema=schema)
    op.drop_index("idx_item_locations_location_id", table_name="item_locations", schema=schema)
    op.drop_index("idx_item_locations_item_id", table_name="item_locations", schema=schema)

    op.drop_table("item_locations", schema=schema)
