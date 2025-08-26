"""create_clean_global_rbac

Revision ID: c40f35611940
Revises: 5ef3b50c709c
Create Date: 2025-08-26 21:20:10.930235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = 'c40f35611940'
down_revision: Union[str, None] = '5ef3b50c709c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create clean global RBAC system with proper foreign key relationships"""
    # Create global_roles table (no JSON permissions)
    op.create_table(
        "global_roles",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="shared",
    )

    # Create global_permissions table with foreign keys
    op.create_table(
        "global_permissions",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["role_id"], ["shared.global_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "resource", "action"),
        schema="shared",
    )

    # Create global_user_roles junction table
    op.create_table(
        "global_user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["shared.global_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["shared.global_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        schema="shared",
    )

    # Create performance indexes
    op.create_index("idx_global_roles_name", "global_roles", ["name"], unique=True, schema="shared")
    op.create_index("idx_global_roles_active", "global_roles", ["is_active"], schema="shared")
    op.create_index("idx_global_permissions_role_id", "global_permissions", ["role_id"], schema="shared")
    op.create_index("idx_global_permissions_resource", "global_permissions", ["resource"], schema="shared")
    op.create_index("idx_global_user_roles_user_id", "global_user_roles", ["user_id"], schema="shared")
    op.create_index("idx_global_user_roles_role_id", "global_user_roles", ["role_id"], schema="shared")

def downgrade() -> None:
    """Remove global RBAC tables"""
    op.drop_index("idx_global_user_roles_role_id", table_name="global_user_roles", schema="shared")
    op.drop_index("idx_global_user_roles_user_id", table_name="global_user_roles", schema="shared")
    op.drop_index("idx_global_permissions_resource", table_name="global_permissions", schema="shared")
    op.drop_index("idx_global_permissions_role_id", table_name="global_permissions", schema="shared")
    op.drop_index("idx_global_roles_active", table_name="global_roles", schema="shared")
    op.drop_index("idx_global_roles_name", table_name="global_roles", schema="shared")
    op.drop_table("global_user_roles", schema="shared")
    op.drop_table("global_permissions", schema="shared")
    op.drop_table("global_roles", schema="shared")
