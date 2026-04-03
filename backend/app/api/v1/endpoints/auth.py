"""
app/api/v1/endpoints/auth.py
Endpoints de autenticación: registro, login, refresh y recuperación de contraseña.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
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
    solicitar_recuperacion,
    resetear_password,
    AuthError,
)
from app.services.email_service import enviar_correo_recuperacion
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()


# ─── Registro ─────────────────────────────────────────────────────────────────


@router.post("/registro", response_model=TokenRespuesta, status_code=201)
async def registro(datos: UsuarioRegistro, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario y retorna los tokens de acceso."""
    try:
        usuario = await registrar_usuario(db, datos)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {
        "access_token": create_access_token(usuario.id),
        "refresh_token": create_refresh_token(usuario.id),
        "usuario": usuario,
    }


# ─── Login ────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenRespuesta)
async def login(datos: UsuarioLogin, db: AsyncSession = Depends(get_db)):
    """Autentica un usuario con username/email y contraseña."""
    try:
        resultado = await login_usuario(db, datos)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado


# ─── Refresh ──────────────────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenRespuesta)
async def refresh(datos: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Genera un nuevo access_token usando un refresh_token válido."""
    try:
        resultado = await refrescar_token(db, datos.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado


# ─── Recuperar contraseña ─────────────────────────────────────────────────────


class RecuperarPasswordRequest(BaseModel):
    email: EmailStr


class ResetearPasswordRequest(BaseModel):
    token: str
    nueva_password: str
    confirmar_password: str


@router.post("/recuperar-password")
async def recuperar_password(
    datos: RecuperarPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Solicita recuperación de contraseña.
    Envía un correo con el enlace. Siempre responde igual por seguridad.
    """
    resultado = await solicitar_recuperacion(db, datos.email)

    if resultado:
        username, email, token = resultado
        enviar_correo_recuperacion(email, token, username)

    return {"mensaje": "Si el correo existe, recibirás un enlace de recuperación."}


@router.post("/resetear-password")
async def resetear_password_endpoint(
    datos: ResetearPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Restablece la contraseña usando el token recibido por correo."""
    if datos.nueva_password != datos.confirmar_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    try:
        await resetear_password(db, datos.token, datos.nueva_password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {
        "mensaje": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."
    }
