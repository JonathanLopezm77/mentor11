"""
app/models/usuario.py
Modelo central del sistema. Representa a todos los tipos de usuario.
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class RolUsuario(str, enum.Enum):
    estudiante       = "estudiante"
    profesor         = "profesor"
    admin_contenido  = "admin_contenido"
    admin_tech       = "admin_tech"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Credenciales ──────────────────────────────────────────────────────────
    username:       Mapped[str] = mapped_column(String(50),  unique=True, nullable=False, index=True)
    email:          Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash:  Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Información personal ──────────────────────────────────────────────────
    fecha_nacimiento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario"),
        nullable=False,
        default=RolUsuario.estudiante,
    )

    # ── Estado y plan ─────────────────────────────────────────────────────────
    es_premium:   Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    esta_activo:  Mapped[bool] = mapped_column(Boolean, default=True,  nullable=False)

    # ── Gamificación ──────────────────────────────────────────────────────────
    racha_actual:   Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    racha_maxima:   Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    puntos_totales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Timestamps ───────────────────────────────────────────────────────────
    ultimo_login:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_registro:  Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # ── Relaciones ───────────────────────────────────────────────────────────
    avatar:            Mapped["Avatar"]              = relationship("Avatar", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    suscripciones:     Mapped[list["Suscripcion"]]   = relationship("Suscripcion", back_populates="usuario", cascade="all, delete-orphan")
    tokens_rec:        Mapped[list["TokenRecuperacion"]] = relationship("TokenRecuperacion", back_populates="usuario", cascade="all, delete-orphan")
    sesiones:          Mapped[list["SesionJuego"]]   = relationship("SesionJuego", back_populates="usuario", foreign_keys="SesionJuego.usuario_id")
    estadisticas:      Mapped[list["EstadisticaUsuario"]] = relationship("EstadisticaUsuario", back_populates="usuario", cascade="all, delete-orphan")
    aulas_creadas:     Mapped[list["Aula"]]          = relationship("Aula", back_populates="profesor", foreign_keys="Aula.profesor_id")
    aulas_inscrito:    Mapped[list["AulaEstudiante"]] = relationship("AulaEstudiante", back_populates="estudiante", foreign_keys="AulaEstudiante.estudiante_id")
    reportes:          Mapped[list["Reporte"]]       = relationship("Reporte", back_populates="usuario", foreign_keys="Reporte.usuario_id")
    notificaciones:    Mapped[list["Notificacion"]]  = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")
    logros_obtenidos:  Mapped[list["UsuarioLogro"]]  = relationship("UsuarioLogro", back_populates="usuario", cascade="all, delete-orphan")
    logs:              Mapped[list["LogActividad"]]  = relationship("LogActividad", back_populates="usuario", foreign_keys="LogActividad.usuario_id")

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} username={self.username!r} rol={self.rol}>"


class Avatar(Base):
    __tablename__ = "avatares"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id:  Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)

    imagen_src:         Mapped[str | None] = mapped_column(Text)
    animal_base:        Mapped[str | None] = mapped_column(String(50))
    accesorio_sombrero: Mapped[str | None] = mapped_column(String(50))
    accesorio_gafas:    Mapped[str | None] = mapped_column(String(50))
    color_primario:     Mapped[str | None] = mapped_column(String(10))
    color_secundario:   Mapped[str | None] = mapped_column(String(10))
    actualizado_en:     Mapped[datetime]   = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="avatar")


class PlanSuscripcion(str, enum.Enum):
    free              = "free"
    premium           = "premium"
    premium_profesor  = "premium_profesor"


class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    plan:              Mapped[PlanSuscripcion] = mapped_column(Enum(PlanSuscripcion, name="plan_suscripcion"), nullable=False)
    fecha_inicio:      Mapped[datetime]        = mapped_column(DateTime, nullable=False)
    fecha_fin:         Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    esta_activa:       Mapped[bool]            = mapped_column(Boolean, default=True)
    metodo_pago:       Mapped[str | None]      = mapped_column(String(50))
    referencia_pago:   Mapped[str | None]      = mapped_column(String(100))

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="suscripciones")


class TokenRecuperacion(Base):
    __tablename__ = "tokens_recuperacion"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    token:      Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    expira_en:  Mapped[datetime] = mapped_column(DateTime, nullable=False)
    usado:      Mapped[bool]     = mapped_column(Boolean, default=False)
    creado_en:  Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="tokens_rec")
