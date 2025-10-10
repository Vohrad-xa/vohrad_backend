"""add_stripe_id_to_tenants

Revision ID: c407f329a627
Revises: 381b222dedd8
Create Date: 2025-10-07 05:20:50.819214

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'c407f329a627'
down_revision: Union[str, None] = '381b222dedd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("stripe_id", sa.String(), nullable=True), schema="shared")


def downgrade() -> None:
    op.drop_column("tenants", "stripe_id", schema="shared")
