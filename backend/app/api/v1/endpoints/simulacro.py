"""
app/api/v1/endpoints/simulacro.py
Endpoints del simulacro ICFES.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.models.simulacro import EstadoSimulacro
from app.services import simulacro_service as svc

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class GuardarProgresoRequest(BaseModel):
    indice_actual: int
    respuestas: dict[str, int]   # {str(pregunta_id): opcion_id}
    tiempo_restante_seg: int


class FinalizarBloqueRequest(BaseModel):
    respuestas: dict[str, int]
    tiempo_restante_seg: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/simulacro/iniciar")
async def iniciar_simulacro(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.iniciar_simulacro(db, usuario.id)
    return _estado_dict(sesion)


@router.get("/simulacro/estado")
async def estado_simulacro(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.obtener_sesion_activa(db, usuario.id)
    if not sesion:
        return {"tiene_simulacro": False}
    return {"tiene_simulacro": True, **_estado_dict(sesion)}


@router.get("/simulacro/{sesion_id}/preguntas")
async def obtener_preguntas(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    preguntas = await svc.obtener_preguntas(db, sesion_id, usuario.id)
    return {"preguntas": preguntas}


@router.post("/simulacro/{sesion_id}/guardar")
async def guardar_progreso(
    sesion_id: int,
    datos: GuardarProgresoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.guardar_progreso(
        db, sesion_id, usuario.id,
        datos.indice_actual, datos.respuestas, datos.tiempo_restante_seg,
    )
    return _estado_dict(sesion)


@router.post("/simulacro/{sesion_id}/pausar")
async def pausar_simulacro(
    sesion_id: int,
    datos: GuardarProgresoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.pausar(
        db, sesion_id, usuario.id,
        datos.indice_actual, datos.respuestas, datos.tiempo_restante_seg,
    )
    return _estado_dict(sesion)


@router.post("/simulacro/{sesion_id}/reanudar")
async def reanudar_simulacro(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.reanudar(db, sesion_id, usuario.id)
    return _estado_dict(sesion)


@router.post("/simulacro/{sesion_id}/finalizar-bloque1")
async def finalizar_bloque1(
    sesion_id: int,
    datos: FinalizarBloqueRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.finalizar_bloque1(
        db, sesion_id, usuario.id, datos.respuestas, datos.tiempo_restante_seg,
    )
    return _estado_dict(sesion)


@router.post("/simulacro/{sesion_id}/iniciar-bloque2")
async def iniciar_bloque2(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.iniciar_bloque2(db, sesion_id, usuario.id)
    return _estado_dict(sesion)


@router.post("/simulacro/{sesion_id}/finalizar")
async def finalizar_simulacro(
    sesion_id: int,
    datos: FinalizarBloqueRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    sesion = await svc.finalizar_simulacro(
        db, sesion_id, usuario.id, datos.respuestas, datos.tiempo_restante_seg,
    )
    return _estado_dict(sesion)


@router.get("/simulacro/{sesion_id}/resultado")
async def resultado_simulacro(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return await svc.obtener_resultado(db, sesion_id, usuario.id)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _estado_dict(sesion) -> dict:
    import json
    ids = json.loads(sesion.preguntas_ids)
    return {
        "sesion_id": sesion.id,
        "estado": sesion.estado,
        "bloque_actual": sesion.bloque_actual,
        "limite_bloque1": sesion.limite_bloque1,
        "total_preguntas": len(ids),
        "indice_actual": sesion.indice_actual,
        "tiempo_restante_b1_seg": sesion.tiempo_restante_b1_seg,
        "tiempo_restante_b2_seg": sesion.tiempo_restante_b2_seg,
        "iniciada_en": sesion.iniciada_en.isoformat() if sesion.iniciada_en else None,
    }
