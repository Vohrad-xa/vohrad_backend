"""add_tokens_valid_after_fields

Revision ID: b8861c920f77
Revises: c40f35611940
Create Date: 2025-09-05 21:05:59.617329

"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "b8861c920f77"
down_revision: Union[str, None] = "c40f35611940"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_tenant_schemas():
    """Get list of existing tenant schemas"""
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT tenant_schema_name FROM shared.tenants WHERE tenant_schema_name != 'shared'"))
    return [row[0] for row in result]


def upgrade() -> None:
    """Add tokens_valid_after field to users table in both shared schema (admins) and all tenant schemas (users)"""
    op.add_column(
        "users",
        sa.Column(
            "tokens_valid_after",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="All tokens issued before this timestamp are invalid",
        ),
        schema="shared",
    )

    op.create_index("idx_users_tokens_valid_after", "users", ["tokens_valid_after"], schema="shared")

    tenant_schemas = get_tenant_schemas()
    for schema_name in tenant_schemas:
        op.add_column(
            "users",
            sa.Column(
                "tokens_valid_after",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="All tokens issued before this timestamp are invalid",
            ),
            schema=schema_name,
        )

        op.create_index("idx_users_tokens_valid_after", "users", ["tokens_valid_after"], schema=schema_name)


def downgrade() -> None:
    """Remove tokens_valid_after field from users table in both shared and tenant schemas"""
    op.drop_index("idx_users_tokens_valid_after", table_name="users", schema="shared")
    op.drop_column("users", "tokens_valid_after", schema="shared")

    tenant_schemas = get_tenant_schemas()
    for schema_name in tenant_schemas:
        op.drop_index("idx_users_tokens_valid_after", table_name="users", schema=schema_name)
        op.drop_column("users", "tokens_valid_after", schema=schema_name)
