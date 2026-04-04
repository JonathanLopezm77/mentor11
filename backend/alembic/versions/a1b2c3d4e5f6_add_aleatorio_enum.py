"""add aleatorio to modo_juego enum

Revision ID: a1b2c3d4e5f6
Revises: fce63bd4729b
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fce63bd4729b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE modo_juego ADD VALUE IF NOT EXISTS 'aleatorio'")


def downgrade() -> None:
    pass
