"""add imagen_url to opciones_respuesta

Revision ID: dc171e7d524a
Revises: e2f3a4b5c6d7
Create Date: 2026-04-06 13:11:25.754536

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dc171e7d524a"
down_revision: Union[str, None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "opciones_respuesta",
        sa.Column("imagen_url", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("opciones_respuesta", "imagen_url")
