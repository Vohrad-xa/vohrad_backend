"""add license_id to tenants table

Revision ID: 381b222dedd8
Revises: 92b6a1ad9cdb
Create Date: 2025-10-07 03:18:46.209754

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '381b222dedd8'
down_revision: Union[str, None] = '92b6a1ad9cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("license_id", sa.UUID(), nullable=True), schema="shared")
    op.create_foreign_key(
        "fk_tenants_license_id_licenses",
        "tenants",
        "licenses",
        ["license_id"],
        ["id"],
        source_schema="shared",
        referent_schema="shared",
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_tenants_license_id_licenses", "tenants", schema="shared", type_="foreignkey")
    op.drop_column("tenants", "license_id", schema="shared")
