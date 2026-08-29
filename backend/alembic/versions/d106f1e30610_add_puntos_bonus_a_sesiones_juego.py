"""add puntos_bonus a sesiones_juego

Revision ID: d106f1e30610
Revises: dc171e7d524a
Create Date: 2026-08-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d106f1e30610"
down_revision: Union[str, None] = "dc171e7d524a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sesiones_juego",
        sa.Column("puntos_bonus", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sesiones_juego",
        sa.Column(
            "ultimo_bonus_checkpoint", sa.Integer(), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    op.drop_column("sesiones_juego", "ultimo_bonus_checkpoint")
    op.drop_column("sesiones_juego", "puntos_bonus")
