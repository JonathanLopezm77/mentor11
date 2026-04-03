"""
app/models/sistema.py
Tablas de soporte: reportes de errores, notificaciones, auditoría y logros.
"""
import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ─── Reportes de contenido / bugs ────────────────────────────────────────────

class TipoReporte(str, enum.Enum):
    error_contenido     = "error_contenido"
    error_tecnico       = "error_tecnico"
    respuesta_incorrecta = "respuesta_incorrecta"
    imagen_rota         = "imagen_rota"
    otro                = "otro"


class EstadoReporte(str, enum.Enum):
    pendiente   = "pendiente"
    en_revision = "en_revision"
    resuelto    = "resuelto"
    descartado  = "descartado"


class Reporte(Base):
    __tablename__ = "reportes"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id:  Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    pregunta_id: Mapped[int | None] = mapped_column(ForeignKey("preguntas.id"), nullable=True)

    tipo:        Mapped[TipoReporte]   = mapped_column(Enum(TipoReporte,   name="tipo_reporte"),   nullable=False)
    descripcion: Mapped[str | None]    = mapped_column(Text)
    estado:      Mapped[EstadoReporte] = mapped_column(Enum(EstadoReporte, name="estado_reporte"), nullable=False, default=EstadoReporte.pendiente)
    resuelto_por: Mapped[int | None]   = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en:   Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    usuario:   Mapped["Usuario"]       = relationship("Usuario", back_populates="reportes",  foreign_keys=[usuario_id])
    pregunta:  Mapped["Pregunta | None"] = relationship("Pregunta", back_populates="reportes")
    resolvente: Mapped["Usuario | None"] = relationship("Usuario", foreign_keys=[resuelto_por])


# ─── Notificaciones ───────────────────────────────────────────────────────────

class TipoNotificacion(str, enum.Enum):
    reto          = "reto"
    meta_diaria   = "meta_diaria"
    nuevo_contenido = "nuevo_contenido"
    racha         = "racha"
    sistema       = "sistema"


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)

    tipo:       Mapped[TipoNotificacion] = mapped_column(Enum(TipoNotificacion, name="tipo_notificacion"), nullable=False)
    titulo:     Mapped[str]              = mapped_column(String(100), nullable=False)
    mensaje:    Mapped[str]              = mapped_column(Text, nullable=False)
    leida:      Mapped[bool]             = mapped_column(Boolean, default=False, nullable=False)
    # dato_extra: metadata flexible, p.ej. {"reto_id": 5, "retador": "juan"}
    dato_extra: Mapped[dict | None]      = mapped_column(JSONB, nullable=True)
    creada_en:  Mapped[datetime]         = mapped_column(DateTime, server_default=func.now())

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="notificaciones")


# ─── Log de actividad (auditoría) ────────────────────────────────────────────

class LogActividad(Base):
    """
    Registro de auditoría para acciones sensibles.
    Usa BIGSERIAL porque crece muy rápido.
    Considerar rotación / archivado periódico en producción.
    """
    __tablename__ = "logs_actividad"

    id:         Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    accion:     Mapped[str]        = mapped_column(String(100), nullable=False)  # ej: "login", "crear_aula", "validar_puntaje"
    entidad:    Mapped[str | None] = mapped_column(String(50))                   # ej: "aula", "partida"
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    ip_origen:  Mapped[str | None] = mapped_column(String(45))                   # Soporta IPv6
    detalle:    Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    creado_en:  Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    usuario: Mapped["Usuario | None"] = relationship("Usuario", back_populates="logs", foreign_keys=[usuario_id])


# ─── Sistema de logros / gamificación ────────────────────────────────────────

class Logro(Base):
    __tablename__ = "logros"

    id:               Mapped[int]        = mapped_column(Integer, primary_key=True)
    nombre:           Mapped[str]        = mapped_column(String(100), nullable=False, unique=True)
    descripcion:      Mapped[str | None] = mapped_column(Text)
    icono_url:        Mapped[str | None] = mapped_column(String(255))
    # condicion_tipo define qué se mide: "racha", "total_correctas", "duelos_ganados", etc.
    condicion_tipo:   Mapped[str | None] = mapped_column(String(50))
    condicion_valor:  Mapped[int | None] = mapped_column(Integer)

    usuarios: Mapped[list["UsuarioLogro"]] = relationship("UsuarioLogro", back_populates="logro")


class UsuarioLogro(Base):
    """Tabla intermedia: qué logros ha obtenido cada usuario."""
    __tablename__ = "usuario_logros"

    usuario_id:   Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    logro_id:     Mapped[int] = mapped_column(ForeignKey("logros.id",   ondelete="CASCADE"), primary_key=True)
    obtenido_en:  Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="logros_obtenidos")
    logro:   Mapped["Logro"]   = relationship("Logro",   back_populates="usuarios")
