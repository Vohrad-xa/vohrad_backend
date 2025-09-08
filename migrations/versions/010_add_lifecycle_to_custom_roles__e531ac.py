"""010_add_lifecycle_to_custom_roles

Revision ID: e531acb63c05
Revises: 7ccfcff71e70
Create Date: 2025-09-09 00:31:43.436780

"""
from alembic import op
from migrations.tenant import for_each_tenant_schema
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "e531acb63c05"
down_revision: Union[str, None] = "7ccfcff71e70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_stage_enum = sa.Enum("ALPHA", "BETA", "GA", "DEPRECATED", "DISABLED", name="role_stage_enum")
    role_stage_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "roles",
        sa.Column(
            "stage",
            role_stage_enum,
            nullable=False,
            server_default="GA",
        ),
        schema="shared",
    )

    _upgrade_tenant_roles()


@for_each_tenant_schema
def _upgrade_tenant_roles(schema: str) -> None:
    op.add_column(
        "roles",
        sa.Column(
            "stage",
            sa.Enum("ALPHA", "BETA", "GA", "DEPRECATED", "DISABLED", name="role_stage_enum"),
            nullable=False,
            server_default="GA",
        ),
        schema=schema,
    )


def downgrade() -> None:
    _downgrade_tenant_roles()
    op.drop_column("roles", "stage", schema="shared")
    role_stage_enum = sa.Enum("ALPHA", "BETA", "GA", "DEPRECATED", "DISABLED", name="role_stage_enum")
    role_stage_enum.drop(op.get_bind(), checkfirst=True)


@for_each_tenant_schema
def _downgrade_tenant_roles(schema: str) -> None:
    op.drop_column("roles", "stage", schema=schema)
