"""
app/services/auth_service.py
Lógica de negocio para registro, login y refresh de tokens.
"""

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.usuario import Usuario, Avatar
from app.schemas.usuario import UsuarioRegistro, UsuarioLogin


# ─── Excepciones propias ──────────────────────────────────────────────────────


class AuthError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


# ─── Registro ─────────────────────────────────────────────────────────────────


async def registrar_usuario(db: AsyncSession, datos: UsuarioRegistro) -> Usuario:
    """
    Crea un nuevo usuario en la base de datos.
    Verifica que el username y email no estén ya en uso.
    """
    # Verificar si ya existe el username o email
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

    # Crear el usuario
    nuevo_usuario = Usuario(
        username=datos.username,
        email=datos.email,
        password_hash=hash_password(datos.password),
        fecha_nacimiento=datos.fecha_nacimiento,
        rol=datos.rol,
    )
    db.add(nuevo_usuario)
    await db.flush()  # flush para obtener el ID sin hacer commit aún

    # Crear avatar vacío por defecto
    avatar = Avatar(usuario_id=nuevo_usuario.id)
    db.add(avatar)

    await db.commit()
    await db.refresh(nuevo_usuario)
    return nuevo_usuario


# ─── Login ────────────────────────────────────────────────────────────────────


async def login_usuario(db: AsyncSession, datos: UsuarioLogin) -> dict:
    """
    Autentica un usuario por username o email + contraseña.
    Retorna los tokens de acceso y refresco.
    """
    # Buscar por username o email
    resultado = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.username == datos.identifier,
                Usuario.email == datos.identifier,
            )
        )
    )
    usuario = resultado.scalar_one_or_none()

    # Verificar que existe y que la contraseña es correcta
    if not usuario or not verify_password(datos.password, usuario.password_hash):
        raise AuthError("Credenciales incorrectas", 401)

    if not usuario.esta_activo:
        raise AuthError("La cuenta está desactivada", 403)

    # Actualizar último login
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
    """
    Genera un nuevo access_token a partir de un refresh_token válido.
    """
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
