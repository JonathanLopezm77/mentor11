"""
app/api/v1/endpoints/perfil.py
Endpoints de perfil del usuario: avatar, estadísticas, edición y contraseña.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, cast
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.usuario import Usuario, Avatar
from app.models.juego import EstadisticaUsuario, RespuestaUsuario, SesionJuego
from app.models.contenido import Materia, Pregunta
from app.services.usuario_service import (
    obtener_perfil, editar_perfil, cambiar_password, UsuarioError
)

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AvatarGuardar(BaseModel):
    imagen_src: str
    animal_base: str | None = None
    accesorio_sombrero: str | None = None
    accesorio_gafas: str | None = None

class AvatarRespuesta(BaseModel):
    imagen_src: str | None = None
    animal_base: str | None = None
    accesorio_sombrero: str | None = None
    accesorio_gafas: str | None = None

class EstadisticaMateria(BaseModel):
    materia: str
    porcentaje: float

class PerfilRespuesta(BaseModel):
    id: int
    username: str
    email: str
    fecha_nacimiento: datetime | None
    rol: str
    es_premium: bool
    racha_actual: int
    racha_maxima: int
    puntos_totales: int
    fecha_registro: datetime
    ultimo_login: datetime | None
    avatar: AvatarRespuesta | None

    model_config = {"from_attributes": True}

class PerfilEditar(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    fecha_nacimiento: datetime | None = None

class CambiarPassword(BaseModel):
    password_actual: str
    password_nuevo: str
    password_nuevo_confirmar: str


# ─── Avatar ───────────────────────────────────────────────────────────────────

@router.get("/avatar", response_model=AvatarRespuesta)
async def obtener_avatar(
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el avatar guardado del usuario."""
    resultado = await db.execute(
        select(Avatar).where(Avatar.usuario_id == usuario.id)
    )
    avatar = resultado.scalar_one_or_none()
    if not avatar:
        return {"imagen_src": None, "animal_base": None, "accesorio_sombrero": None, "accesorio_gafas": None}
    return {
        "imagen_src": avatar.imagen_src,
        "animal_base": avatar.animal_base,
        "accesorio_sombrero": avatar.accesorio_sombrero,
        "accesorio_gafas": avatar.accesorio_gafas,
    }


@router.put("/avatar", response_model=AvatarRespuesta)
async def guardar_avatar(
    datos: AvatarGuardar,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Guarda o actualiza el avatar del usuario."""
    resultado = await db.execute(
        select(Avatar).where(Avatar.usuario_id == usuario.id)
    )
    avatar = resultado.scalar_one_or_none()

    if avatar:
        avatar.imagen_src = datos.imagen_src
        avatar.animal_base = datos.animal_base
        avatar.accesorio_sombrero = datos.accesorio_sombrero
        avatar.accesorio_gafas = datos.accesorio_gafas
    else:
        avatar = Avatar(
            usuario_id=usuario.id,
            imagen_src=datos.imagen_src,
            animal_base=datos.animal_base,
            accesorio_sombrero=datos.accesorio_sombrero,
            accesorio_gafas=datos.accesorio_gafas,
        )
        db.add(avatar)

    await db.commit()
    return {
        "imagen_src": datos.imagen_src,
        "animal_base": datos.animal_base,
        "accesorio_sombrero": datos.accesorio_sombrero,
        "accesorio_gafas": datos.accesorio_gafas,
    }


# ─── Estadísticas ─────────────────────────────────────────────────────────────

@router.get("/estadisticas", response_model=list[EstadisticaMateria])
async def obtener_estadisticas(
    periodo: Optional[str] = Query(None, regex="^(dia|semana|mes)$"),
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el porcentaje de acierto por materia del usuario.
    Si se pasa ?periodo=dia|semana|mes filtra por respuestas recientes.
    Sin periodo devuelve el acumulado histórico.
    """
    if periodo:
        ahora = datetime.now(timezone.utc)
        if periodo == "dia":
            desde = ahora - timedelta(days=1)
        elif periodo == "semana":
            desde = ahora - timedelta(weeks=1)
        else:  # mes
            desde = ahora - timedelta(days=30)

        resultado = await db.execute(
            select(
                Materia.nombre,
                func.count(RespuestaUsuario.id).label("total"),
                func.sum(cast(RespuestaUsuario.es_correcta, Integer)).label("correctas"),
            )
            .join(SesionJuego, RespuestaUsuario.sesion_id == SesionJuego.id)
            .join(Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id)
            .join(Materia, Pregunta.materia_id == Materia.id)
            .where(
                SesionJuego.usuario_id == usuario.id,
                RespuestaUsuario.respondida_en >= desde,
            )
            .group_by(Materia.nombre)
            .order_by(Materia.nombre)
        )
        filas = resultado.all()
        return [
            {
                "materia": nombre,
                "porcentaje": round((correctas / total) * 100) if total else 0,
            }
            for nombre, total, correctas in filas
            if total > 0
        ]

    # Sin filtro: acumulado histórico
    resultado = await db.execute(
        select(EstadisticaUsuario, Materia.nombre)
        .join(Materia, EstadisticaUsuario.materia_id == Materia.id)
        .where(
            EstadisticaUsuario.usuario_id == usuario.id,
            EstadisticaUsuario.total_respondidas > 0,
        )
        .order_by(Materia.nombre)
    )
    filas = resultado.all()
    return [
        {"materia": nombre, "porcentaje": est.porcentaje_acierto}
        for est, nombre in filas
    ]


# ─── Ver perfil ───────────────────────────────────────────────────────────────

@router.get("/me", response_model=PerfilRespuesta)
async def ver_perfil(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Devuelve el perfil completo del usuario autenticado."""
    try:
        return await obtener_perfil(db, usuario.id)
    except UsuarioError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Editar perfil ────────────────────────────────────────────────────────────

@router.put("/me", response_model=PerfilRespuesta)
async def actualizar_perfil(
    datos: PerfilEditar,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Edita username, email o fecha de nacimiento. Solo se actualizan los campos enviados."""
    try:
        return await editar_perfil(db, usuario.id, datos.model_dump(exclude_none=True))
    except UsuarioError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Cambiar contraseña ───────────────────────────────────────────────────────

@router.put("/me/password")
async def actualizar_password(
    datos: CambiarPassword,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Cambia la contraseña. Requiere la contraseña actual para confirmar identidad."""
    try:
        return await cambiar_password(db, usuario.id, datos.model_dump())
    except UsuarioError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)