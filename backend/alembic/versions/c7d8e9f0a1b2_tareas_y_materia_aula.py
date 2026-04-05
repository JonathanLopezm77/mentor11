"""tareas y materia_id en aulas

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar materia_id a la tabla aulas
    op.add_column('aulas', sa.Column('materia_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_aulas_materia_id', 'aulas', 'materias', ['materia_id'], ['id']
    )

    # Crear tabla tareas
    op.create_table(
        'tareas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aula_id', sa.Integer(), nullable=False),
        sa.Column('cantidad_preguntas', sa.Integer(), nullable=False),
        sa.Column('creada_en', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['aula_id'], ['aulas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tareas_id'), 'tareas', ['id'], unique=False)
    op.create_index(op.f('ix_tareas_aula_id'), 'tareas', ['aula_id'], unique=False)

    # Crear tabla tarea_progreso
    op.create_table(
        'tarea_progreso',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tarea_id', sa.Integer(), nullable=False),
        sa.Column('estudiante_id', sa.Integer(), nullable=False),
        sa.Column('sesion_id', sa.Integer(), nullable=True),
        sa.Column('completada', sa.Boolean(), nullable=False),
        sa.Column('iniciada_en', sa.DateTime(), nullable=True),
        sa.Column('completada_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['estudiante_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sesion_id'], ['sesiones_juego.id']),
        sa.ForeignKeyConstraint(['tarea_id'], ['tareas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tarea_id', 'estudiante_id', name='uq_tarea_estudiante'),
    )
    op.create_index(op.f('ix_tarea_progreso_id'), 'tarea_progreso', ['id'], unique=False)
    op.create_index(op.f('ix_tarea_progreso_tarea_id'), 'tarea_progreso', ['tarea_id'], unique=False)


def downgrade() -> None:
    op.drop_table('tarea_progreso')
    op.drop_table('tareas')
    op.drop_constraint('fk_aulas_materia_id', 'aulas', type_='foreignkey')
    op.drop_column('aulas', 'materia_id')
