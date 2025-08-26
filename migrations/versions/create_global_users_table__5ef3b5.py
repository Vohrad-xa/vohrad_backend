"""create_global_users_table

Revision ID: 5ef3b50c709c
Revises: a5b98cda4300
Create Date: 2025-08-26 20:47:44.716827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = '5ef3b50c709c'
down_revision: Union[str, None] = 'a5b98cda4300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create global users table in shared schema"""
    op.create_table(
        "global_users",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("role IN ('super_admin', 'admin', 'support')", name="check_global_user_role"),
        schema="shared",
    )

    # Create indexes for performance
    op.create_index("idx_global_users_email", "global_users", ["email"], unique=True, schema="shared")
    op.create_index("idx_global_users_role", "global_users", ["role"], schema="shared")
    op.create_index("idx_global_users_active", "global_users", ["is_active"], schema="shared")

def downgrade() -> None:
    """Drop global users table from shared schema"""
    op.drop_index("idx_global_users_active", table_name="global_users", schema="shared")
    op.drop_index("idx_global_users_role", table_name="global_users", schema="shared")
    op.drop_index("idx_global_users_email", table_name="global_users", schema="shared")
    op.drop_table("global_users", schema="shared")
