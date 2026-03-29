"""
app/api/v1/endpoints/auth.py
Endpoints de autenticación: registro, login y refresh de token.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.usuario import (
    UsuarioRegistro,
    UsuarioLogin,
    TokenRespuesta,
    RefreshRequest,
)
from app.services.auth_service import (
    registrar_usuario,
    login_usuario,
    refrescar_token,
    AuthError,
)

router = APIRouter()


@router.post("/registro", response_model=TokenRespuesta, status_code=201)
async def registro(datos: UsuarioRegistro, db: AsyncSession = Depends(get_db)):
    """
    Registra un nuevo usuario y retorna los tokens de acceso.
    """
    try:
        usuario = await registrar_usuario(db, datos)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {
        "access_token": __import__(
            "app.core.security", fromlist=["create_access_token"]
        ).create_access_token(usuario.id),
        "refresh_token": __import__(
            "app.core.security", fromlist=["create_refresh_token"]
        ).create_refresh_token(usuario.id),
        "usuario": usuario,
    }


@router.post("/login", response_model=TokenRespuesta)
async def login(datos: UsuarioLogin, db: AsyncSession = Depends(get_db)):
    """
    Autentica un usuario con username/email y contraseña.
    Retorna access_token y refresh_token.
    """
    try:
        resultado = await login_usuario(db, datos)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado


@router.post("/refresh", response_model=TokenRespuesta)
async def refresh(datos: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Genera un nuevo access_token usando un refresh_token válido.
    Usar cuando el access_token expire (cada 60 minutos).
    """
    try:
        resultado = await refrescar_token(db, datos.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado
