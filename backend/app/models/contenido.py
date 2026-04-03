"""
app/models/contenido.py
Banco de preguntas: materias, textos, preguntas, respuestas y pistas.
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TipoPregunta(str, enum.Enum):
    opcion_multiple = "opcion_multiple"
    lectura_critica = "lectura_critica"
    matematica      = "matematica"


class NivelDificultad(str, enum.Enum):
    facil   = "facil"
    medio   = "medio"
    dificil = "dificil"


class Materia(Base):
    __tablename__ = "materias"

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True)
    nombre:       Mapped[str]       = mapped_column(String(100), nullable=False)
    codigo_icfes: Mapped[str | None] = mapped_column(String(20))
    descripcion:  Mapped[str | None] = mapped_column(Text)
    icono_url:    Mapped[str | None] = mapped_column(String(255))
    color_hex:    Mapped[str | None] = mapped_column(String(10))
    esta_activa:  Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    preguntas:    Mapped[list["Pregunta"]]          = relationship("Pregunta", back_populates="materia")
    textos:       Mapped[list["Texto"]]             = relationship("Texto", back_populates="materia")
    estadisticas: Mapped[list["EstadisticaUsuario"]] = relationship("EstadisticaUsuario", back_populates="materia")

    def __repr__(self) -> str:
        return f"<Materia id={self.id} nombre={self.nombre!r}>"


class Texto(Base):
    """
    Pasaje o fragmento de lectura al que pueden vincularse varias preguntas.
    Útil para Lectura Crítica e Inglés donde un texto tiene múltiples ítems.
    """
    __tablename__ = "textos"

    id:          Mapped[int]       = mapped_column(Integer, primary_key=True)
    materia_id:  Mapped[int | None] = mapped_column(ForeignKey("materias.id"), nullable=True)
    titulo:      Mapped[str | None] = mapped_column(String(255))
    contenido:   Mapped[str]        = mapped_column(Text, nullable=False)
    fuente:      Mapped[str | None] = mapped_column(String(255))
    esta_activo: Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)
    creado_en:   Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    materia:   Mapped["Materia | None"]  = relationship("Materia", back_populates="textos")
    preguntas: Mapped[list["Pregunta"]]  = relationship("Pregunta", back_populates="texto")


class Pregunta(Base):
    __tablename__ = "preguntas"

    id:         Mapped[int]       = mapped_column(Integer, primary_key=True, index=True)
    materia_id: Mapped[int]       = mapped_column(ForeignKey("materias.id"), nullable=False, index=True)
    texto_id:   Mapped[int | None] = mapped_column(ForeignKey("textos.id"), nullable=True)
    creada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    enunciado:        Mapped[str]            = mapped_column(Text, nullable=False)
    imagen_url:       Mapped[str | None]     = mapped_column(String(255))
    tipo:             Mapped[TipoPregunta]   = mapped_column(Enum(TipoPregunta,    name="tipo_pregunta"),    nullable=False)
    nivel_dificultad: Mapped[NivelDificultad] = mapped_column(Enum(NivelDificultad, name="nivel_dificultad"), nullable=False, default=NivelDificultad.medio)
    competencia:      Mapped[str | None]     = mapped_column(String(100))

    # Explicación básica (free). La IA (premium) se genera dinámicamente.
    explicacion_texto: Mapped[str | None] = mapped_column(Text)

    # Métricas para calcular dificultad dinámica
    veces_respondida: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    veces_incorrecta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    esta_activa: Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    creada_en:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    materia:    Mapped["Materia"]          = relationship("Materia", back_populates="preguntas")
    texto:      Mapped["Texto | None"]     = relationship("Texto", back_populates="preguntas")
    respuestas: Mapped[list["Respuesta"]]  = relationship("Respuesta", back_populates="pregunta", cascade="all, delete-orphan")
    pistas:     Mapped[list["Pista"]]      = relationship("Pista", back_populates="pregunta", cascade="all, delete-orphan")
    reportes:   Mapped[list["Reporte"]]    = relationship("Reporte", back_populates="pregunta")
    respuestas_usuarios: Mapped[list["RespuestaUsuario"]] = relationship("RespuestaUsuario", back_populates="pregunta")

    @property
    def porcentaje_error(self) -> float:
        if self.veces_respondida == 0:
            return 0.0
        return round((self.veces_incorrecta / self.veces_respondida) * 100, 2)

    def __repr__(self) -> str:
        return f"<Pregunta id={self.id} materia_id={self.materia_id} tipo={self.tipo}>"


class Respuesta(Base):
    """
    Opción de respuesta para una pregunta.
    Sin letra fija: el backend asigna A/B/C/D aleatoriamente al servir.
    """
    __tablename__ = "opciones_respuesta"

    id:          Mapped[int]  = mapped_column(Integer, primary_key=True)
    pregunta_id: Mapped[int]  = mapped_column(ForeignKey("preguntas.id", ondelete="CASCADE"), nullable=False, index=True)
    texto:       Mapped[str]  = mapped_column(Text, nullable=False)
    es_correcta: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relaciones
    pregunta:           Mapped["Pregunta"]              = relationship("Pregunta", back_populates="respuestas")
    respuestas_usuario: Mapped[list["RespuestaUsuario"]] = relationship("RespuestaUsuario", back_populates="opcion_elegida")


class Pista(Base):
    __tablename__ = "pistas"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    pregunta_id: Mapped[int] = mapped_column(ForeignKey("preguntas.id", ondelete="CASCADE"), nullable=False)

    texto_pista: Mapped[str] = mapped_column(Text, nullable=False)
    orden:       Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    pregunta: Mapped["Pregunta"] = relationship("Pregunta", back_populates="pistas")
