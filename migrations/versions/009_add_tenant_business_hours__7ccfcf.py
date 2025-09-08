"""add tenant business hours columns

Revision ID: 7ccfcff71e70
Revises: b8861c920f77
Create Date: 2025-09-08 22:39:45.549591

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "7ccfcff71e70"
down_revision: Union[str, None] = "b8861c920f77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add business hours columns to shared.tenants."""
    op.add_column(
        "tenants",
        sa.Column("business_hour_start", sa.Integer(), nullable=True),
        schema="shared",
    )
    op.add_column(
        "tenants",
        sa.Column("business_hour_end", sa.Integer(), nullable=True),
        schema="shared",
    )


def downgrade() -> None:
    """Remove business hours columns from shared.tenants."""
    op.drop_column("tenants", "business_hour_end", schema="shared")
    op.drop_column("tenants", "business_hour_start", schema="shared")
