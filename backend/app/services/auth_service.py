"""
app/services/auth_service.py
Lógica de negocio para registro, login, refresh y recuperación de contraseña.
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.usuario import Usuario, Avatar, TokenRecuperacion
from app.schemas.usuario import UsuarioRegistro, UsuarioLogin


class AuthError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


# ─── Registro ─────────────────────────────────────────────────────────────────


async def registrar_usuario(db: AsyncSession, datos: UsuarioRegistro) -> Usuario:
    resultado = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.username == datos.username,
                Usuario.email == datos.email,
            )
        )
    )
    existente = resultado.scalar_one_or_none()

    if existente:
        if existente.username == datos.username:
            raise AuthError("El nombre de usuario ya está en uso", 409)
        raise AuthError("El email ya está registrado", 409)

    nuevo_usuario = Usuario(
        username=datos.username,
        email=datos.email,
        password_hash=hash_password(datos.password),
        fecha_nacimiento=datos.fecha_nacimiento,
        rol=datos.rol,
    )
    db.add(nuevo_usuario)
    await db.flush()

    avatar = Avatar(usuario_id=nuevo_usuario.id)
    db.add(avatar)

    await db.commit()
    await db.refresh(nuevo_usuario)
    return nuevo_usuario


# ─── Login ────────────────────────────────────────────────────────────────────


async def login_usuario(db: AsyncSession, datos: UsuarioLogin) -> dict:
    resultado = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.username == datos.identifier,
                Usuario.email == datos.identifier,
            )
        )
    )
    usuario = resultado.scalar_one_or_none()

    if not usuario or not verify_password(datos.password, usuario.password_hash):
        raise AuthError("Credenciales incorrectas", 401)

    if not usuario.esta_activo:
        raise AuthError("La cuenta está desactivada", 403)

    usuario.ultimo_login = datetime.utcnow()
    await db.commit()
    await db.refresh(usuario)

    return {
        "access_token": create_access_token(usuario.id),
        "refresh_token": create_refresh_token(usuario.id),
        "usuario": usuario,
    }


# ─── Refresh token ────────────────────────────────────────────────────────────


async def refrescar_token(db: AsyncSession, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise AuthError("Token de refresco inválido o expirado", 401)

    usuario_id = payload.get("sub")
    resultado = await db.execute(select(Usuario).where(Usuario.id == int(usuario_id)))
    usuario = resultado.scalar_one_or_none()

    if not usuario or not usuario.esta_activo:
        raise AuthError("Usuario no encontrado o desactivado", 401)

    return {
        "access_token": create_access_token(usuario.id),
        "refresh_token": create_refresh_token(usuario.id),
        "usuario": usuario,
    }


# ─── Recuperación de contraseña ───────────────────────────────────────────────


async def solicitar_recuperacion(db: AsyncSession, email: str):
    """
    Genera un token de recuperación y lo guarda en la BD.
    Retorna (username, email, token) si el usuario existe, None si no.
    """
    resultado = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario = resultado.scalar_one_or_none()

    if not usuario:
        return None

    # Invalidar tokens anteriores
    tokens_anteriores = await db.execute(
        select(TokenRecuperacion).where(
            TokenRecuperacion.usuario_id == usuario.id,
            TokenRecuperacion.usado == False,
        )
    )
    for token_viejo in tokens_anteriores.scalars().all():
        token_viejo.usado = True

    # Crear nuevo token con expiración de 30 minutos
    token = secrets.token_urlsafe(32)
    expira = datetime.utcnow() + timedelta(minutes=30)

    nuevo_token = TokenRecuperacion(
        usuario_id=usuario.id,
        token=token,
        expira_en=expira,
        usado=False,
    )
    db.add(nuevo_token)
    await db.commit()

    return usuario.username, usuario.email, token


async def resetear_password(db: AsyncSession, token: str, nueva_password: str) -> None:
    """
    Verifica el token y actualiza la contraseña del usuario.
    """
    resultado = await db.execute(
        select(TokenRecuperacion).where(
            TokenRecuperacion.token == token,
            TokenRecuperacion.usado == False,
        )
    )
    token_obj = resultado.scalar_one_or_none()

    if not token_obj:
        raise AuthError("Token inválido o ya utilizado", 400)

    if token_obj.expira_en < datetime.utcnow():
        raise AuthError("El token ha expirado. Solicita uno nuevo.", 400)

    resultado_usuario = await db.execute(
        select(Usuario).where(Usuario.id == token_obj.usuario_id)
    )
    usuario = resultado_usuario.scalar_one_or_none()
    if not usuario:
        raise AuthError("Usuario no encontrado", 404)

    if len(nueva_password) < 8:
        raise AuthError("La contraseña debe tener al menos 8 caracteres", 400)

    usuario.password_hash = hash_password(nueva_password)
    token_obj.usado = True
    await db.commit()
