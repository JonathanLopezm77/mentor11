"""
app/models/juego.py
Todo lo relacionado con partidas, respuestas, estadísticas y el modo online.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ModoJuego(str, enum.Enum):
    libre = "libre"
    arcade = "arcade"
    contrareloj = "contrareloj"
    aleatorio = "aleatorio"
    online_tradicional = "online_tradicional"
    online_poderes = "online_poderes"
    online_arcade = "online_arcade"


class SesionJuego(Base):
    """
    Registra cada sesión de práctica o partida jugada.
    En el modo online, se crea una sesión por jugador y se enlazan en PartidaOnline.
    """

    __tablename__ = "sesiones_juego"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )

    modo_juego: Mapped[ModoJuego] = mapped_column(
        Enum(ModoJuego, name="modo_juego"), nullable=False
    )
    puntaje_obtenido: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_preguntas: Mapped[int | None] = mapped_column(Integer)
    total_correctas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pistas_usadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duracion_segundos: Mapped[int | None] = mapped_column(Integer)
    completada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    iniciada_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relaciones
    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="sesiones", foreign_keys=[usuario_id]
    )
    respuestas: Mapped[list["RespuestaUsuario"]] = relationship(
        "RespuestaUsuario", back_populates="sesion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SesionJuego id={self.id} usuario_id={self.usuario_id} modo={self.modo_juego}>"


class RespuestaUsuario(Base):
    """
    Cada respuesta individual dada por un usuario en una sesión.
    Es la tabla más creciente del sistema — considerar particionado a futuro.
    """

    __tablename__ = "respuestas_usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sesion_id: Mapped[int] = mapped_column(
        ForeignKey("sesiones_juego.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pregunta_id: Mapped[int] = mapped_column(
        ForeignKey("preguntas.id"), nullable=False, index=True
    )
    opcion_elegida_id: Mapped[int | None] = mapped_column(
        ForeignKey("opciones_respuesta.id"), nullable=True
    )

    es_correcta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    uso_pista: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    solicito_ia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tiempo_respuesta_ms: Mapped[int | None] = mapped_column(Integer)
    respondida_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    sesion: Mapped["SesionJuego"] = relationship(
        "SesionJuego", back_populates="respuestas"
    )
    pregunta: Mapped["Pregunta"] = relationship(
        "Pregunta", back_populates="respuestas_usuarios"
    )
    opcion_elegida: Mapped["Respuesta | None"] = relationship(
        "Respuesta", back_populates="respuestas_usuario"
    )


class EstadisticaUsuario(Base):
    """
    Acumulado de rendimiento por usuario/materia.
    Se actualiza al finalizar cada sesión (no en tiempo real para evitar locks).
    """

    __tablename__ = "estadisticas_usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    materia_id: Mapped[int] = mapped_column(ForeignKey("materias.id"), nullable=False)

    total_respondidas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_correctas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    porcentaje_acierto: Mapped[float] = mapped_column(
        Integer, default=0, nullable=False
    )
    ultima_sesion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="estadisticas")
    materia: Mapped["Materia"] = relationship("Materia", back_populates="estadisticas")

    __table_args__ = (
        # Un usuario tiene máximo una fila por materia
        {"sqlite_autoincrement": False},
    )


# ─── Modo Online ──────────────────────────────────────────────────────────────


class ModoPartida(str, enum.Enum):
    tradicional = "tradicional"
    poderes = "poderes"
    arcade = "arcade"


class EstadoPartida(str, enum.Enum):
    buscando = "buscando"
    en_curso = "en_curso"
    finalizada = "finalizada"
    cancelada = "cancelada"


class PartidaOnline(Base):
    """
    Representa un duelo en tiempo real entre dos jugadores.
    Cada jugador tiene su propia SesionJuego asociada.
    """

    __tablename__ = "partidas_online"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jugador1_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    jugador2_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )  # NULL mientras busca oponente
    sesion_j1_id: Mapped[int | None] = mapped_column(
        ForeignKey("sesiones_juego.id"), nullable=True
    )
    sesion_j2_id: Mapped[int | None] = mapped_column(
        ForeignKey("sesiones_juego.id"), nullable=True
    )
    ganador_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )

    modo: Mapped[ModoPartida] = mapped_column(
        Enum(ModoPartida, name="modo_partida"), nullable=False
    )
    estado: Mapped[EstadoPartida] = mapped_column(
        Enum(EstadoPartida, name="estado_partida"),
        nullable=False,
        default=EstadoPartida.buscando,
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    jugador1: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[jugador1_id])
    jugador2: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[jugador2_id]
    )
    ganador: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[ganador_id]
    )
    poderes: Mapped[list["PoderPartida"]] = relationship(
        "PoderPartida", back_populates="partida", cascade="all, delete-orphan"
    )
    retos: Mapped[list["Reto"]] = relationship("Reto", back_populates="partida")


class PoderPartida(Base):
    """Poderes asignados aleatoriamente al inicio de una partida en Modo Poderes."""

    __tablename__ = "poderes_partida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partidas_online.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    tipo_poder: Mapped[str] = mapped_column(String(50), nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    partida: Mapped["PartidaOnline"] = relationship(
        "PartidaOnline", back_populates="poderes"
    )
