"""indices y unique constraint en estadisticas_usuario/respuestas_usuario (PERF-01, PERF-02)

Revision ID: f3b7d9a1c5e2
Revises: e8a9c2f1b4d3
Create Date: 2026-08-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f3b7d9a1c5e2"
down_revision: Union[str, None] = "e8a9c2f1b4d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── PERF-02: antes de crear la constraint única, verificar que no haya
    # duplicados ya guardados (usuario_id, materia_id). Si los hay, se
    # detiene con un mensaje claro en vez de intentarlo a ciegas — fusionar
    # filas duplicadas es una decisión sobre datos reales que no me
    # corresponde tomar sola en una migración automática.
    duplicados = conn.execute(
        sa.text(
            """
            SELECT usuario_id, materia_id, COUNT(*) AS n
            FROM estadisticas_usuario
            GROUP BY usuario_id, materia_id
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicados:
        detalle = ", ".join(f"(usuario_id={d.usuario_id}, materia_id={d.materia_id})" for d in duplicados)
        raise RuntimeError(
            "No se puede aplicar la migración: existen filas duplicadas en "
            f"estadisticas_usuario para: {detalle}. Hay que decidir manualmente "
            "cómo fusionarlas (sumar totales, cuál conservar) antes de poder "
            "agregar la constraint única. Esta migración no las tocó."
        )

    # ── PERF-01: índices en las columnas más consultadas ──────────────────
    op.create_index("ix_estadisticas_usuario_usuario_id", "estadisticas_usuario", ["usuario_id"])
    op.create_index("ix_estadisticas_usuario_materia_id", "estadisticas_usuario", ["materia_id"])
    op.create_index("ix_respuestas_usuario_respondida_en", "respuestas_usuario", ["respondida_en"])

    # ── PERF-02: constraint única real (antes solo existía en un comentario) ──
    op.create_unique_constraint(
        "uq_estadistica_usuario_materia", "estadisticas_usuario", ["usuario_id", "materia_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_estadistica_usuario_materia", "estadisticas_usuario", type_="unique")
    op.drop_index("ix_respuestas_usuario_respondida_en", table_name="respuestas_usuario")
    op.drop_index("ix_estadisticas_usuario_materia_id", table_name="estadisticas_usuario")
    op.drop_index("ix_estadisticas_usuario_usuario_id", table_name="estadisticas_usuario")
