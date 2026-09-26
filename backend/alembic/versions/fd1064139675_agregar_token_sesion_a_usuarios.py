"""agregar token_sesion a usuarios

Revision ID: fd1064139675
Revises: f3b7d9a1c5e2
Create Date: 2026-09-19 22:33:03.717216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd1064139675'
down_revision: Union[str, None] = 'f3b7d9a1c5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('token_sesion', sa.String(length=36), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'token_sesion')