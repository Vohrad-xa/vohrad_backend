"""add_missing_tenant_columns

Revision ID: ead5e1c6d28f
Revises: 4647208018d3
Create Date: 2025-08-22 01:27:42.611682

"""

import sqlalchemy as sa
from alembic import op
from typing import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "ead5e1c6d28f"
down_revision: Union[str, None] = "4647208018d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("email", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("telephone", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("street", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("street_number", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("city", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("province", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("postal_code", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("remarks", sa.Text(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("website", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("logo", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("industry", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("tax_id", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("billing_address", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("country", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("timezone", sa.String(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("settings", sa.JSON(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("created_by", sa.UUID(), nullable=True), schema="shared")
    op.add_column(
        "tenants", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), schema="shared"
    )
    op.add_column(
        "tenants", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), schema="shared"
    )
    op.add_column("tenants", sa.Column("deleted_at", sa.DateTime(), nullable=True), schema="shared")
    op.add_column("tenants", sa.Column("status", sa.String(), nullable=False, server_default="active"), schema="shared")
    op.execute("UPDATE shared.tenants SET status = current_status::text")
    op.drop_column("tenants", "current_status", schema="shared")

    op.create_index("idx_tenants_sub_domain", "tenants", ["sub_domain"], unique=True, schema="shared")
    op.create_index("idx_tenants_status", "tenants", ["status"], schema="shared")
    op.create_index("idx_tenants_email", "tenants", ["email"], schema="shared")
    op.create_index("idx_tenants_created_at", "tenants", ["created_at"], schema="shared")
    op.create_index("idx_tenants_created_by", "tenants", ["created_by"], schema="shared")
    op.create_index("idx_tenants_deleted_at", "tenants", ["deleted_at"], schema="shared")
    op.create_index("idx_tenants_status_deleted", "tenants", ["status", "deleted_at"], schema="shared")


def downgrade() -> None:
    op.drop_index("idx_tenants_status_deleted", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_deleted_at", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_created_by", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_created_at", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_email", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_status", table_name="tenants", schema="shared")
    op.drop_index("idx_tenants_sub_domain", table_name="tenants", schema="shared")
    op.add_column(
        "tenants",
        sa.Column(
            "current_status",
            sa.Enum("active", "inactive", name="status", schema="shared", inherit_schema=True),
            nullable=False,
        ),
        schema="shared",
    )
    op.execute("UPDATE shared.tenants SET current_status = status::shared.status")
    op.drop_column("tenants", "status", schema="shared")
    op.drop_column("tenants", "deleted_at", schema="shared")
    op.drop_column("tenants", "updated_at", schema="shared")
    op.drop_column("tenants", "created_at", schema="shared")
    op.drop_column("tenants", "created_by", schema="shared")
    op.drop_column("tenants", "settings", schema="shared")
    op.drop_column("tenants", "timezone", schema="shared")
    op.drop_column("tenants", "country", schema="shared")
    op.drop_column("tenants", "billing_address", schema="shared")
    op.drop_column("tenants", "tax_id", schema="shared")
    op.drop_column("tenants", "industry", schema="shared")
    op.drop_column("tenants", "logo", schema="shared")
    op.drop_column("tenants", "website", schema="shared")
    op.drop_column("tenants", "remarks", schema="shared")
    op.drop_column("tenants", "postal_code", schema="shared")
    op.drop_column("tenants", "province", schema="shared")
    op.drop_column("tenants", "city", schema="shared")
    op.drop_column("tenants", "street_number", schema="shared")
    op.drop_column("tenants", "street", schema="shared")
    op.drop_column("tenants", "telephone", schema="shared")
    op.drop_column("tenants", "email", schema="shared")
