"""create_users_table

Revision ID: a5b98cda4300
Revises: ead5e1c6d28f
Create Date: 2025-08-24 21:29:37.309705

"""

import sqlalchemy as sa
from alembic import op
from migrations.tenant import for_each_tenant_schema
from typing import Sequence
from typing import Union


# revision identifiers, used by Alembic.
revision: str = "a5b98cda4300"
down_revision: Union[str, None] = "ead5e1c6d28f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@for_each_tenant_schema
def upgrade(schema: str) -> None:
    """Create users table in each tenant schema"""
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("first_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=True),
        sa.Column("tenant_role", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("postal_code", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("remember_token", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["shared.tenants.tenant_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("email"),
        schema=schema,
    )

    # Create indexes
    op.create_index("idx_users_tenant_id", "users", ["tenant_id"], schema=schema)
    op.create_index("idx_users_tenant_id_id", "users", ["tenant_id", "id"], schema=schema)


@for_each_tenant_schema
def downgrade(schema: str) -> None:
    """Drop users table from each tenant schema"""
    op.drop_index("idx_users_tenant_id_id", table_name="users", schema=schema)
    op.drop_index("idx_users_tenant_id", table_name="users", schema=schema)
    op.drop_table("users", schema=schema)
