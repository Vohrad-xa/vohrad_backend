"""017_create_attachments_and_attachables_tables

Revision ID: b0642a810786
Revises: c407f329a627
Create Date: 2025-10-14 19:52:52.043979

"""
from alembic import op
from migrations.tenant import for_each_tenant_schema
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'b0642a810786'
down_revision: Union[str, None] = 'c407f329a627'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@for_each_tenant_schema
def upgrade(schema: str) -> None:
    # Create attachments table
    op.create_table(
        "attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column("extension", sa.String(10), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], [f"{schema}.users.id"], ondelete="SET NULL"),
        schema=schema,
    )

    op.create_index("idx_attachments_user_id", "attachments", ["user_id"], schema=schema)
    op.create_index("idx_attachments_category", "attachments", ["category"], schema=schema)
    op.create_index("idx_attachments_file_type", "attachments", ["file_type"], schema=schema)
    op.create_index("idx_attachments_created_at", "attachments", ["created_at"], schema=schema)
    op.create_index("idx_attachments_deleted_at", "attachments", ["deleted_at"], schema=schema)
    op.create_check_constraint(
        "ck_attachments_size_non_negative",
        "attachments",
        "size >= 0",
        schema=schema,
    )

    # Create attachables table
    op.create_table(
        "attachables",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("attachment_id", sa.UUID(), nullable=False),
        sa.Column("attachable_type", sa.String(50), nullable=False),
        sa.Column("attachable_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["attachment_id"], [f"{schema}.attachments.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("attachment_id", "attachable_type", "attachable_id", name="attachables_unique"),
        schema=schema,
    )

    op.create_index("idx_attachables_type_id", "attachables", ["attachable_type", "attachable_id"], schema=schema)
    op.create_index("idx_attachables_attachment_id", "attachables", ["attachment_id"], schema=schema)
    op.create_check_constraint(
        "ck_attachables_type_supported",
        "attachables",
        "attachable_type IN ('item','location','item_location')",
        schema=schema,
    )


@for_each_tenant_schema
def downgrade(schema: str) -> None:
    # Drop attachables table
    op.drop_constraint("ck_attachables_type_supported", "attachables", type_="check", schema=schema)
    op.drop_index("idx_attachables_attachment_id", table_name="attachables", schema=schema)
    op.drop_index("idx_attachables_type_id", table_name="attachables", schema=schema)
    op.drop_table("attachables", schema=schema)

    # Drop attachments table
    op.drop_constraint("ck_attachments_size_non_negative", "attachments", type_="check", schema=schema)
    op.drop_index("idx_attachments_deleted_at", table_name="attachments", schema=schema)
    op.drop_index("idx_attachments_created_at", table_name="attachments", schema=schema)
    op.drop_index("idx_attachments_file_type", table_name="attachments", schema=schema)
    op.drop_index("idx_attachments_category", table_name="attachments", schema=schema)
    op.drop_index("idx_attachments_user_id", table_name="attachments", schema=schema)
    op.drop_table("attachments", schema=schema)
