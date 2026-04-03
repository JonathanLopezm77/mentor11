"""
app/core/deps.py
Dependencias reutilizables de FastAPI.
La más importante: get_current_user — protege endpoints con JWT.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app.db.database import get_db
from app.models.usuario import Usuario

# Esquema de seguridad Bearer Token para Swagger
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Dependencia que extrae y valida el JWT del header Authorization.
    Uso en un endpoint:
        async def mi_endpoint(usuario: Usuario = Depends(get_current_user)):
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_id = payload.get("sub")
    resultado = await db.execute(select(Usuario).where(Usuario.id == int(usuario_id)))
    usuario = resultado.scalar_one_or_none()

    if not usuario or not usuario.esta_activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o desactivado",
        )

    return usuario


async def get_admin(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Verifica que el usuario autenticado tenga rol admin_tech.
    Uso: admin: Usuario = Depends(get_admin)
    """
    if usuario.rol != "admin_tech":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido al panel de administración",
        )
    return usuario
