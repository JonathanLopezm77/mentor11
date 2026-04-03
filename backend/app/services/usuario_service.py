"""
app/services/usuario_service.py
Lógica de negocio para el perfil del usuario.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario, Avatar
from app.core.security import verify_password, hash_password


class UsuarioError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


async def _cargar_usuario(db: AsyncSession, usuario_id: int) -> Usuario:
    resultado = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.avatar))
        .where(Usuario.id == usuario_id)
    )
    return resultado.scalar_one_or_none()


# ─── Ver perfil ───────────────────────────────────────────────────────────────

async def obtener_perfil(db: AsyncSession, usuario_id: int) -> Usuario:
    usuario = await _cargar_usuario(db, usuario_id)
    if not usuario:
        raise UsuarioError("Usuario no encontrado", 404)
    return usuario


# ─── Editar perfil ────────────────────────────────────────────────────────────

async def editar_perfil(db: AsyncSession, usuario_id: int, datos: dict) -> Usuario:
    usuario = await _cargar_usuario(db, usuario_id)
    if not usuario:
        raise UsuarioError("Usuario no encontrado", 404)

    if datos.get("username") and datos["username"] != usuario.username:
        existe = await db.execute(
            select(Usuario).where(Usuario.username == datos["username"])
        )
        if existe.scalar_one_or_none():
            raise UsuarioError("Ese nombre de usuario ya está en uso", 409)
        usuario.username = datos["username"]

    if datos.get("email") and datos["email"] != usuario.email:
        existe = await db.execute(
            select(Usuario).where(Usuario.email == datos["email"])
        )
        if existe.scalar_one_or_none():
            raise UsuarioError("Ese correo ya está registrado", 409)
        usuario.email = datos["email"]

    if datos.get("fecha_nacimiento") is not None:
        fecha = datos["fecha_nacimiento"]
        if hasattr(fecha, "tzinfo") and fecha.tzinfo is not None:
            fecha = fecha.replace(tzinfo=None)
        usuario.fecha_nacimiento = fecha

    await db.commit()
    return await _cargar_usuario(db, usuario_id)


# ─── Cambiar contraseña ───────────────────────────────────────────────────────

async def cambiar_password(db: AsyncSession, usuario_id: int, datos: dict) -> dict:
    usuario = await _cargar_usuario(db, usuario_id)
    if not usuario:
        raise UsuarioError("Usuario no encontrado", 404)

    if not verify_password(datos["password_actual"], usuario.password_hash):
        raise UsuarioError("La contraseña actual es incorrecta", 400)

    if datos["password_nuevo"] != datos["password_nuevo_confirmar"]:
        raise UsuarioError("Las contraseñas nuevas no coinciden", 400)

    if len(datos["password_nuevo"]) < 8:
        raise UsuarioError("La contraseña debe tener al menos 8 caracteres", 400)

    usuario.password_hash = hash_password(datos["password_nuevo"])
    await db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}