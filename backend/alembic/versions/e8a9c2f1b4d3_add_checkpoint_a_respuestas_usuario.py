"""add checkpoint a respuestas_usuario

Revision ID: e8a9c2f1b4d3
Revises: d106f1e30610
Create Date: 2026-08-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e8a9c2f1b4d3"
down_revision: Union[str, None] = "d106f1e30610"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "respuestas_usuario",
        sa.Column("checkpoint", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_respuestas_usuario_checkpoint",
        "respuestas_usuario",
        ["checkpoint"],
    )


def downgrade() -> None:
    op.drop_index("ix_respuestas_usuario_checkpoint", table_name="respuestas_usuario")
    op.drop_column("respuestas_usuario", "checkpoint")
