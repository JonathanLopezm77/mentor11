"""
app/schemas/usuario.py
Esquemas Pydantic para validación de datos de usuario y autenticación.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.usuario import RolUsuario


# ─── Registro ─────────────────────────────────────────────────────────────────


class UsuarioRegistro(BaseModel):
    username: str
    email: EmailStr
    password: str
    fecha_nacimiento: datetime | None = None
    rol: RolUsuario = RolUsuario.estudiante

    @field_validator("username")
    @classmethod
    def username_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        if len(v) > 50:
            raise ValueError("El username no puede superar 50 caracteres")
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                "El username solo puede contener letras, números, puntos y guiones bajos"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


# ─── Login ────────────────────────────────────────────────────────────────────


class UsuarioLogin(BaseModel):
    # Acepta username o email
    identifier: str
    password: str


# ─── Respuestas ───────────────────────────────────────────────────────────────


class UsuarioRespuesta(BaseModel):
    id: int
    username: str
    email: str
    rol: RolUsuario
    es_premium: bool
    racha_actual: int
    puntos_totales: int
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class TokenRespuesta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioRespuesta


class RefreshRequest(BaseModel):
    refresh_token: str
