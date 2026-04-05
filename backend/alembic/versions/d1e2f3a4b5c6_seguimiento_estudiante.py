"""seguimiento_estudiante en aula_estudiantes

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-05 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'aula_estudiantes',
        sa.Column('en_seguimiento', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('aula_estudiantes', 'en_seguimiento')
