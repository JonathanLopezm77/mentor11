"""
app/models/aula.py
Gestión de aulas virtuales del profesor, ranking y sistema de retos.
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Aula(Base):
    __tablename__ = "aulas"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profesor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)

    nombre:        Mapped[str]        = mapped_column(String(100), nullable=False)
    codigo_acceso: Mapped[str]        = mapped_column(String(10), unique=True, nullable=False, index=True)
    descripcion:   Mapped[str | None] = mapped_column(Text)
    color_hex:     Mapped[str | None] = mapped_column(String(10))
    esta_activa:   Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)
    creada_en:     Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    profesor:    Mapped["Usuario"]             = relationship("Usuario", back_populates="aulas_creadas", foreign_keys=[profesor_id])
    estudiantes: Mapped[list["AulaEstudiante"]] = relationship("AulaEstudiante", back_populates="aula", cascade="all, delete-orphan")
    rankings:    Mapped[list["RankingAula"]]   = relationship("RankingAula", back_populates="aula", cascade="all, delete-orphan")
    retos:       Mapped[list["Reto"]]          = relationship("Reto", back_populates="aula")

    def __repr__(self) -> str:
        return f"<Aula id={self.id} nombre={self.nombre!r} codigo={self.codigo_acceso!r}>"


class AulaEstudiante(Base):
    """Tabla intermedia — relación muchos-a-muchos entre Aula y Usuario."""
    __tablename__ = "aula_estudiantes"

    aula_id:      Mapped[int] = mapped_column(ForeignKey("aulas.id",    ondelete="CASCADE"), primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)

    fecha_union: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    esta_activo: Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    aula:       Mapped["Aula"]    = relationship("Aula",    back_populates="estudiantes")
    estudiante: Mapped["Usuario"] = relationship("Usuario", back_populates="aulas_inscrito", foreign_keys=[estudiante_id])


class PeriodoRanking(str, enum.Enum):
    semanal  = "semanal"
    mensual  = "mensual"


class RankingAula(Base):
    """
    Ranking de estudiantes dentro de un aula.
    Se recalcula periódicamente (semanal/mensual) mediante un job en background.
    """
    __tablename__ = "ranking_aula"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    aula_id:     Mapped[int] = mapped_column(ForeignKey("aulas.id",    ondelete="CASCADE"), nullable=False, index=True)
    usuario_id:  Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    periodo:              Mapped[PeriodoRanking] = mapped_column(Enum(PeriodoRanking, name="periodo_ranking"), nullable=False)
    puntos:               Mapped[int]    = mapped_column(Integer, default=0, nullable=False)
    posicion:             Mapped[int | None] = mapped_column(Integer)
    fecha_inicio_periodo: Mapped[datetime | None] = mapped_column(DateTime)
    actualizado_en:       Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones
    aula:    Mapped["Aula"]    = relationship("Aula",    back_populates="rankings")
    usuario: Mapped["Usuario"] = relationship("Usuario")

    __table_args__ = (
        UniqueConstraint("aula_id", "usuario_id", "periodo", "fecha_inicio_periodo", name="uq_ranking_periodo"),
    )


class EstadoReto(str, enum.Enum):
    pendiente  = "pendiente"
    aceptado   = "aceptado"
    rechazado  = "rechazado"
    expirado   = "expirado"


class Reto(Base):
    """Desafío directo entre dos estudiantes del mismo aula."""
    __tablename__ = "retos"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    retador_id:  Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    retado_id:   Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    aula_id:     Mapped[int | None] = mapped_column(ForeignKey("aulas.id"), nullable=True)
    partida_id:  Mapped[int | None] = mapped_column(ForeignKey("partidas_online.id"), nullable=True)

    estado:    Mapped[EstadoReto] = mapped_column(Enum(EstadoReto, name="estado_reto"), nullable=False, default=EstadoReto.pendiente)
    expira_en: Mapped[datetime]   = mapped_column(DateTime, nullable=False)
    creado_en: Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    retador:  Mapped["Usuario"]          = relationship("Usuario", foreign_keys=[retador_id])
    retado:   Mapped["Usuario"]          = relationship("Usuario", foreign_keys=[retado_id])
    aula:     Mapped["Aula | None"]      = relationship("Aula",    back_populates="retos")
    partida:  Mapped["PartidaOnline | None"] = relationship("PartidaOnline", back_populates="retos")
