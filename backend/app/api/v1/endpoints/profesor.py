"""
app/api/v1/endpoints/profesor.py
Endpoints para profesores (aulas, tareas, rankings) y para estudiantes (unirse, tareas).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.schemas.aula import (
    CrearAulaRequest,
    AulaRespuesta,
    UnirseAulaRequest,
    CrearTareaRequest,
    TareaRespuesta,
    RankingAulaRespuesta,
    StatsGrupo,
    StatsIndividual,
    AulaDetalleRespuesta,
    TareaEstudianteRespuesta,
)
from app.services.aula_service import (
    crear_aula,
    listar_aulas_profesor,
    detalle_aula,
    ranking_aula,
    stats_grupo,
    stats_estudiante,
    crear_tarea,
    unirse_a_aula,
    listar_aulas_estudiante,
    iniciar_tarea,
    completar_tarea,
    marcar_seguimiento,
    listar_seguimientos_profesor,
    AulaError,
)

router = APIRouter()


def _requerir_profesor(usuario: Usuario):
    if usuario.rol != RolUsuario.profesor and usuario.rol != RolUsuario.admin_contenido and usuario.rol != RolUsuario.admin_tech:
        raise HTTPException(status_code=403, detail="Solo los profesores pueden acceder a este recurso")


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE PROFESOR
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/profesor/aulas", status_code=201)
async def crear_aula_endpoint(
    datos: CrearAulaRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        aula = await crear_aula(db, usuario.id, datos.nombre, datos.materia_id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)
    return {
        "id": aula.id,
        "nombre": aula.nombre,
        "codigo_acceso": aula.codigo_acceso,
        "materia_id": aula.materia_id,
        "mensaje": "Aula creada correctamente",
    }


@router.get("/profesor/aulas")
async def listar_aulas_profesor_endpoint(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    return await listar_aulas_profesor(db, usuario.id)


@router.get("/profesor/aulas/{aula_id}")
async def detalle_aula_endpoint(
    aula_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await detalle_aula(db, aula_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.post("/profesor/aulas/{aula_id}/tareas", status_code=201)
async def crear_tarea_endpoint(
    aula_id: int,
    datos: CrearTareaRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await crear_tarea(db, aula_id, usuario.id, datos.cantidad_preguntas)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.get("/profesor/aulas/{aula_id}/ranking")
async def ranking_endpoint(
    aula_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await ranking_aula(db, aula_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.get("/profesor/aulas/{aula_id}/stats")
async def stats_grupo_endpoint(
    aula_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await stats_grupo(db, aula_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.get("/profesor/aulas/{aula_id}/estudiantes/{est_id}/stats")
async def stats_estudiante_endpoint(
    aula_id: int,
    est_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await stats_estudiante(db, aula_id, est_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.put("/profesor/aulas/{aula_id}/estudiantes/{est_id}/seguimiento")
async def toggle_seguimiento(
    aula_id: int,
    est_id: int,
    marcar: bool,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    try:
        return await marcar_seguimiento(db, aula_id, est_id, usuario.id, marcar)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.get("/profesor/seguimiento")
async def seguimiento_endpoint(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _requerir_profesor(usuario)
    return await listar_seguimientos_profesor(db, usuario.id)


@router.get("/profesor/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Stats rápidas para el dashboard del profesor."""
    _requerir_profesor(usuario)
    aulas = await listar_aulas_profesor(db, usuario.id)
    total_estudiantes = sum(a["total_estudiantes"] for a in aulas)
    return {
        "aulas": len(aulas),
        "estudiantes": total_estudiantes,
        "retos": 0,
        "estudiantes_lista": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE ESTUDIANTE
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/estudiante/aulas/unirse", status_code=200)
async def unirse_endpoint(
    datos: UnirseAulaRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        return await unirse_a_aula(db, usuario.id, datos.codigo)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.get("/estudiante/aulas")
async def listar_aulas_estudiante_endpoint(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return await listar_aulas_estudiante(db, usuario.id)


@router.post("/estudiante/tareas/{tarea_id}/iniciar")
async def iniciar_tarea_endpoint(
    tarea_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        return await iniciar_tarea(db, tarea_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


@router.post("/estudiante/tareas/{tarea_id}/completar")
async def completar_tarea_endpoint(
    tarea_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        return await completar_tarea(db, tarea_id, usuario.id)
    except AulaError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)
