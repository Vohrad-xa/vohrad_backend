"""create licenses table in shared schema

Revision ID: 92b6a1ad9cdb
Revises: 64abac85073e
Create Date: 2025-10-07 03:08:47.378996

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '92b6a1ad9cdb'
down_revision: Union[str, None] = '64abac85073e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "licenses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("seats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("license_key", sa.String(length=256), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="inactive"),
        sa.Column("features", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("meta", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_licenses")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["shared.tenants.tenant_id"],
            name=op.f("fk_licenses_tenant_id_tenants"),
            ondelete="CASCADE"
            ),
        schema="shared",
    )
    op.create_index("idx_licenses_tenant_id", "licenses", ["tenant_id"], schema="shared")
    op.create_index("idx_licenses_license_key", "licenses", ["license_key"], unique=True, schema="shared")
    op.create_index("idx_licenses_status", "licenses", ["status"], schema="shared")
    op.create_index("idx_licenses_starts_at", "licenses", ["starts_at"], schema="shared")
    op.create_index("idx_licenses_ends_at", "licenses", ["ends_at"], schema="shared")


def downgrade() -> None:
    op.drop_index("idx_licenses_ends_at", table_name="licenses", schema="shared")
    op.drop_index("idx_licenses_starts_at", table_name="licenses", schema="shared")
    op.drop_index("idx_licenses_status", table_name="licenses", schema="shared")
    op.drop_index("idx_licenses_license_key", table_name="licenses", schema="shared")
    op.drop_index("idx_licenses_tenant_id", table_name="licenses", schema="shared")
    op.drop_table("licenses", schema="shared")
