"""simulacro_sesion

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-05 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF NOT EXISTS evita el error si el tipo ya existía de una migración parcial
    op.execute("""
        CREATE TYPE IF NOT EXISTS estado_simulacro AS ENUM ('activo', 'pausado', 'entre_bloques', 'completado')
    """)
    op.create_table(
        'simulacro_sesiones',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True),
        # create_type=False: el tipo ya fue creado arriba, SQLAlchemy no debe intentarlo de nuevo
        sa.Column('estado', sa.Enum('activo', 'pausado', 'entre_bloques', 'completado', name='estado_simulacro', create_type=False), nullable=False, server_default='activo'),
        sa.Column('bloque_actual', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('limite_bloque1', sa.Integer(), nullable=False, server_default='91'),
        sa.Column('preguntas_ids', sa.Text(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column('respuestas', sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('indice_actual', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tiempo_restante_b1_seg', sa.Integer(), nullable=False, server_default='10800'),
        sa.Column('tiempo_restante_b2_seg', sa.Integer(), nullable=False, server_default='10800'),
        sa.Column('iniciada_en', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completada_en', sa.DateTime(), nullable=True),
        sa.Column('ultimo_guardado_en', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('simulacro_sesiones')
    op.execute("DROP TYPE IF EXISTS estado_simulacro")
