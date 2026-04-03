"""imagen_src to Text

Revision ID: b3f1a2c4d5e6
Revises: ea1777ad591a
Create Date: 2026-03-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3f1a2c4d5e6'
down_revision: Union[str, None] = 'ea1777ad591a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'avatares', 'imagen_src',
        existing_type=sa.String(length=200),
        type_=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'avatares', 'imagen_src',
        existing_type=sa.Text(),
        type_=sa.String(length=200),
        nullable=True,
    )
