"""create_items_table

Revision ID: 191f2520080d
Revises: e531acb63c05
Create Date: 2025-10-02 18:43:00.688792

"""
from alembic import op
from migrations.tenant import for_each_tenant_schema
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '191f2520080d'
down_revision: Union[str, None] = 'e531acb63c05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@for_each_tenant_schema
def upgrade(schema: str) -> None:
    preparer = sa.sql.compiler.IdentifierPreparer(op.get_bind().dialect)
    schema_quoted = preparer.format_schema(schema)

    # Create tracking_mode enum type
    op.execute(f"CREATE TYPE {schema_quoted}.tracking_mode_enum AS ENUM ('abstract', 'standard', 'serialized')")

    # Create items table
    op.create_table(
        "items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("barcode", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tracking_mode", sa.String(), nullable=False, server_default="abstract"),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("serial_number", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("specifications", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("estimated_value", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("tracking_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_change_reason", sa.Text(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("parent_item_id", sa.UUID(), nullable=True),
        sa.Column("item_relation_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], [f"{schema}.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_item_id"], [f"{schema}.items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_relation_id"], [f"{schema}.items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("code", name="items_code_unique"),
        sa.UniqueConstraint("serial_number", name="items_serial_number_unique"),
        sa.CheckConstraint("tracking_mode IN ('abstract', 'standard', 'serialized')", name="items_tracking_mode_check"),
        schema=schema,
    )

    # Create indexes
    op.create_index("idx_items_code", "items", ["code"], schema=schema)
    op.create_index("idx_items_barcode", "items", ["barcode"], schema=schema)
    op.create_index("idx_items_tracking_mode", "items", ["tracking_mode"], schema=schema)
    op.create_index("idx_items_serial_number", "items", ["serial_number"], schema=schema)
    op.create_index("idx_items_user_id", "items", ["user_id"], schema=schema)
    op.create_index("idx_items_parent_item_id", "items", ["parent_item_id"], schema=schema)
    op.create_index("idx_items_item_relation_id", "items", ["item_relation_id"], schema=schema)
    op.create_index("idx_items_is_active", "items", ["is_active"], schema=schema)
    op.create_index("idx_items_created_at", "items", ["created_at"], schema=schema)


@for_each_tenant_schema
def downgrade(schema: str) -> None:
    preparer = sa.sql.compiler.IdentifierPreparer(op.get_bind().dialect)
    schema_quoted = preparer.format_schema(schema)

    # Drop indexes
    op.drop_index("idx_items_created_at", table_name="items", schema=schema)
    op.drop_index("idx_items_is_active", table_name="items", schema=schema)
    op.drop_index("idx_items_item_relation_id", table_name="items", schema=schema)
    op.drop_index("idx_items_parent_item_id", table_name="items", schema=schema)
    op.drop_index("idx_items_user_id", table_name="items", schema=schema)
    op.drop_index("idx_items_serial_number", table_name="items", schema=schema)
    op.drop_index("idx_items_tracking_mode", table_name="items", schema=schema)
    op.drop_index("idx_items_barcode", table_name="items", schema=schema)
    op.drop_index("idx_items_code", table_name="items", schema=schema)

    # Drop items table
    op.drop_table("items", schema=schema)

    # Drop tracking_mode enum type
    op.execute(f"DROP TYPE IF EXISTS {schema_quoted}.tracking_mode_enum")
