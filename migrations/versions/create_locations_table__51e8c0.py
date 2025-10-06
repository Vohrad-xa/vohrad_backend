"""create locations table

Revision ID: 51e8c0f63cd7
Revises: 191f2520080d
Create Date: 2025-10-05 02:29:28.920631

"""
from alembic import op
from migrations.tenant import for_each_tenant_schema
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '51e8c0f63cd7'
down_revision: Union[str, None] = '191f2520080d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@for_each_tenant_schema
def upgrade(schema: str) -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], [f"{schema}.locations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="locations_code_unique"),
        schema=schema,
    )

    op.create_index("idx_locations_parent_id", "locations", ["parent_id"], schema=schema)
    op.create_index("idx_locations_is_active", "locations", ["is_active"], schema=schema)
    op.create_index("idx_locations_path", "locations", ["path"], schema=schema)


@for_each_tenant_schema
def downgrade(schema: str) -> None:
    op.drop_index("idx_locations_path", table_name="locations", schema=schema)
    op.drop_index("idx_locations_is_active", table_name="locations", schema=schema)
    op.drop_index("idx_locations_parent_id", table_name="locations", schema=schema)

    op.drop_table("locations", schema=schema)
