"""add scores jsonb to saved_products

Revision ID: a1b2c3d4e5f6
Revises: 47908d53e46e
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '47908d53e46e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('saved_products', sa.Column('scores', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('saved_products', 'scores')
