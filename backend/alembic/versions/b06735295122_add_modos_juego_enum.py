"""add modos juego enum

Revision ID: b06735295122
Revises: b3f1a2c4d5e6
Create Date: 2026-03-31 00:18:47.250288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b06735295122'
down_revision: Union[str, None] = 'b3f1a2c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The init migration had a typo ('contrarreloj' with double-r) and was
    # missing 'aleatorio'. This migration adds the correct values safely.
    op.execute("ALTER TYPE modo_juego ADD VALUE IF NOT EXISTS 'aleatorio'")
    op.execute("ALTER TYPE modo_juego ADD VALUE IF NOT EXISTS 'contrareloj'")


def downgrade() -> None:
    # Postgres does not support removing enum values — no downgrade possible.
    pass
