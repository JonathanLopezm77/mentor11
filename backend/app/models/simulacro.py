"""
app/models/simulacro.py
Simulacro ICFES — sesión con dos bloques de 3 horas y guardado de progreso.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EstadoSimulacro(str, enum.Enum):
    activo = "activo"              # jugando (bloque 1 o 2)
    pausado = "pausado"            # pausado dentro de un bloque
    entre_bloques = "entre_bloques"  # bloque 1 terminado, descanso
    completado = "completado"      # ambos bloques terminados


class SimulacroSesion(Base):
    __tablename__ = "simulacro_sesiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    estado: Mapped[EstadoSimulacro] = mapped_column(
        Enum(EstadoSimulacro, name="estado_simulacro"),
        nullable=False,
        default=EstadoSimulacro.activo,
    )
    bloque_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Índice donde empieza el bloque 2 (número de preguntas del bloque 1)
    limite_bloque1: Mapped[int] = mapped_column(Integer, nullable=False, default=91)

    # JSON: [id1, id2, ...]  — IDs de preguntas en orden (bloque1 + bloque2)
    preguntas_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # JSON: {"pregunta_id": opcion_elegida_id, ...}
    respuestas: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    indice_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tiempo_restante_b1_seg: Mapped[int] = mapped_column(Integer, nullable=False, default=10800)
    tiempo_restante_b2_seg: Mapped[int] = mapped_column(Integer, nullable=False, default=10800)

    iniciada_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ultimo_guardado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    usuario: Mapped["Usuario"] = relationship("Usuario")
