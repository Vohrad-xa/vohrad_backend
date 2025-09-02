"""create_clean_global_rbac

Revision ID: c40f35611940
Revises: 5ef3b50c709c
Create Date: 2025-08-26 21:20:10.930235

"""
import sqlalchemy as sa
from alembic import op
from typing import Sequence
from typing import Union
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = 'c40f35611940'
down_revision: Union[str, None] = '5ef3b50c709c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_tenant_schemas():
    """Get list of existing tenant schemas"""
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT tenant_schema_name FROM shared.tenants WHERE tenant_schema_name != 'shared'")
    )
    return [row[0] for row in result]


def create_auth_tables_for_schema(schema_name: str, user_table_name: str):
    """Create roles, permissions, and assignments tables for a specific schema"""
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("role_type", sa.Enum(
            "basic", "predefined", name="role_type_enum"), nullable=False, server_default="predefined"),
        sa.Column("role_scope", sa.Enum(
            "global", "tenant", name="role_scope_enum"), nullable=False, server_default="tenant"),
        sa.Column("is_mutable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("permissions_mutable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("managed_by", sa.String(length=50), nullable=True),
        sa.Column("is_deletable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema=schema_name,
    )

    # Create permissions table with foreign keys
    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["role_id"], [f"{schema_name}.roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "resource", "action"),
        schema=schema_name,
    )

    # Create assignments junction table
    op.create_table(
        "assignments",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], [f"{schema_name}.{user_table_name}.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], [f"{schema_name}.roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        schema=schema_name,
    )

    op.create_index(f"idx_roles_name_{schema_name}", "roles", ["name"], unique=True, schema=schema_name)
    op.create_index(f"idx_roles_active_{schema_name}", "roles", ["is_active"], schema=schema_name)
    op.create_index(f"idx_permissions_role_id_{schema_name}", "permissions", ["role_id"], schema=schema_name)
    op.create_index(f"idx_permissions_resource_{schema_name}", "permissions", ["resource"], schema=schema_name)
    op.create_index(f"idx_assignments_user_id_{schema_name}", "assignments", ["user_id"], schema=schema_name)
    op.create_index(f"idx_assignments_role_id_{schema_name}", "assignments", ["role_id"], schema=schema_name)
    op.create_index(
        f"idx_permissions_resource_action_{schema_name}",
        "permissions",
        ["resource", "action"],
        schema=schema_name
    )
    op.create_index(
        f"idx_permissions_role_resource_{schema_name}",
        "permissions",
        ["role_id", "resource"],
        schema=schema_name
    )
    op.create_index(f"idx_roles_active_name_{schema_name}", "roles", ["is_active", "name"], schema=schema_name)


def drop_auth_tables_for_schema(schema_name: str):
    """Drop roles, permissions, and assignments tables for a specific schema"""
    op.drop_index(f"idx_roles_active_name_{schema_name}", table_name="roles", schema=schema_name)
    op.drop_index(f"idx_permissions_role_resource_{schema_name}", table_name="permissions", schema=schema_name)
    op.drop_index(f"idx_permissions_resource_action_{schema_name}", table_name="permissions", schema=schema_name)

    op.drop_index(f"idx_assignments_role_id_{schema_name}", table_name="assignments", schema=schema_name)
    op.drop_index(f"idx_assignments_user_id_{schema_name}", table_name="assignments", schema=schema_name)
    op.drop_index(f"idx_permissions_resource_{schema_name}", table_name="permissions", schema=schema_name)
    op.drop_index(f"idx_permissions_role_id_{schema_name}", table_name="permissions", schema=schema_name)
    op.drop_index(f"idx_roles_active_{schema_name}", table_name="roles", schema=schema_name)
    op.drop_index(f"idx_roles_name_{schema_name}", table_name="roles", schema=schema_name)

    op.drop_table("assignments", schema=schema_name)
    op.drop_table("permissions", schema=schema_name)
    op.drop_table("roles", schema=schema_name)


def upgrade() -> None:
    """Create RBAC tables for both shared schema (admins) and all tenant schemas (users)"""
    # Create auth tables for shared schema (for admins)
    create_auth_tables_for_schema("shared", "admins")

    # Create auth tables for all existing tenant schemas (for users)
    tenant_schemas = get_tenant_schemas()
    for schema_name in tenant_schemas:
        create_auth_tables_for_schema(schema_name, "users")


def downgrade() -> None:
    """Remove RBAC tables from both shared and tenant schemas"""
    drop_auth_tables_for_schema("shared")
    tenant_schemas = get_tenant_schemas()
    for schema_name in tenant_schemas:
        drop_auth_tables_for_schema(schema_name)
