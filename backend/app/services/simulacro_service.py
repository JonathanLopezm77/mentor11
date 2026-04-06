"""
app/services/simulacro_service.py
Lógica de negocio del simulacro ICFES.
"""

import json
import random
from datetime import datetime

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contenido import Materia, Pregunta, Respuesta
from app.models.simulacro import SimulacroSesion, EstadoSimulacro

# Distribución oficial ICFES Saber 11
# Bloque 1 (3 h): Lectura Crítica + Matemáticas
# Bloque 2 (3 h): Ciencias Naturales + Sociales + Inglés
_DIST_B1 = [("LC", 41), ("MAT", 50)]
_DIST_B2 = [("CN", 58), ("SOC", 50), ("ING", 55)]


async def _seleccionar_ids(db: AsyncSession) -> tuple[list[int], int]:
    """Devuelve (lista_de_ids_ordenada, limite_bloque1)."""
    ids_b1, ids_b2 = [], []

    for codigo, cantidad in _DIST_B1:
        res = await db.execute(
            select(Pregunta.id)
            .join(Materia, Pregunta.materia_id == Materia.id)
            .where(Materia.codigo_icfes == codigo, Pregunta.esta_activa == True)
            .order_by(func.random())
            .limit(cantidad)
        )
        ids_b1.extend([r[0] for r in res.all()])

    for codigo, cantidad in _DIST_B2:
        res = await db.execute(
            select(Pregunta.id)
            .join(Materia, Pregunta.materia_id == Materia.id)
            .where(Materia.codigo_icfes == codigo, Pregunta.esta_activa == True)
            .order_by(func.random())
            .limit(cantidad)
        )
        ids_b2.extend([r[0] for r in res.all()])

    return ids_b1 + ids_b2, len(ids_b1)


async def obtener_sesion_activa(db: AsyncSession, usuario_id: int) -> SimulacroSesion | None:
    res = await db.execute(
        select(SimulacroSesion)
        .where(
            SimulacroSesion.usuario_id == usuario_id,
            SimulacroSesion.estado != EstadoSimulacro.completado,
        )
        .order_by(SimulacroSesion.iniciada_en.desc())
        .limit(1)
    )
    return res.scalar_one_or_none()


async def iniciar_simulacro(db: AsyncSession, usuario_id: int) -> SimulacroSesion:
    """Crea un nuevo simulacro. Si hay uno activo/pausado lo devuelve sin crear otro."""
    existente = await obtener_sesion_activa(db, usuario_id)
    if existente:
        return existente

    ids, limite = await _seleccionar_ids(db)
    sesion = SimulacroSesion(
        usuario_id=usuario_id,
        estado=EstadoSimulacro.activo,
        bloque_actual=1,
        limite_bloque1=limite,
        preguntas_ids=json.dumps(ids),
        respuestas="{}",
        indice_actual=0,
        tiempo_restante_b1_seg=10800,
        tiempo_restante_b2_seg=10800,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def obtener_preguntas(
    db: AsyncSession, sesion_id: int, usuario_id: int
) -> list[dict]:
    """Devuelve la lista completa de preguntas con opciones (sin marcar la correcta)."""
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    ids = json.loads(sesion.preguntas_ids)
    if not ids:
        return []

    res = await db.execute(
        select(Pregunta)
        .options(selectinload(Pregunta.respuestas), selectinload(Pregunta.materia))
        .where(Pregunta.id.in_(ids))
    )
    preguntas_map = {p.id: p for p in res.scalars().all()}

    resultado = []
    for pid in ids:
        p = preguntas_map.get(pid)
        if not p:
            continue
        opciones = list(p.respuestas)
        random.shuffle(opciones)
        letras = "ABCD"
        resultado.append({
            "id": p.id,
            "materia": p.materia.nombre if p.materia else "",
            "materia_codigo": p.materia.codigo_icfes if p.materia else "",
            "enunciado": p.enunciado,
            "opciones": [
                {"id": op.id, "letra": letras[i], "texto": op.texto}
                for i, op in enumerate(opciones[:4])
            ],
        })
    return resultado


async def guardar_progreso(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    indice_actual: int,
    respuestas: dict,
    tiempo_restante_seg: int,
) -> SimulacroSesion:
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    sesion.indice_actual = indice_actual
    sesion.respuestas = json.dumps({str(k): v for k, v in respuestas.items()})
    if sesion.bloque_actual == 1:
        sesion.tiempo_restante_b1_seg = max(0, tiempo_restante_seg)
    else:
        sesion.tiempo_restante_b2_seg = max(0, tiempo_restante_seg)
    sesion.ultimo_guardado_en = datetime.utcnow()
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def pausar(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    indice_actual: int,
    respuestas: dict,
    tiempo_restante_seg: int,
) -> SimulacroSesion:
    sesion = await guardar_progreso(
        db, sesion_id, usuario_id, indice_actual, respuestas, tiempo_restante_seg
    )
    sesion.estado = EstadoSimulacro.pausado
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def reanudar(
    db: AsyncSession, sesion_id: int, usuario_id: int
) -> SimulacroSesion:
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    if sesion.estado == EstadoSimulacro.pausado:
        sesion.estado = EstadoSimulacro.activo
        await db.commit()
        await db.refresh(sesion)
    return sesion


async def finalizar_bloque1(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    respuestas: dict,
    tiempo_restante_seg: int,
) -> SimulacroSesion:
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    sesion.respuestas = json.dumps({str(k): v for k, v in respuestas.items()})
    sesion.tiempo_restante_b1_seg = max(0, tiempo_restante_seg)
    sesion.estado = EstadoSimulacro.entre_bloques
    sesion.ultimo_guardado_en = datetime.utcnow()
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def iniciar_bloque2(
    db: AsyncSession, sesion_id: int, usuario_id: int
) -> SimulacroSesion:
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    sesion.estado = EstadoSimulacro.activo
    sesion.bloque_actual = 2
    sesion.indice_actual = sesion.limite_bloque1
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def finalizar_simulacro(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    respuestas: dict,
    tiempo_restante_seg: int,
) -> SimulacroSesion:
    sesion = await _get_sesion(db, sesion_id, usuario_id)
    sesion.respuestas = json.dumps({str(k): v for k, v in respuestas.items()})
    sesion.tiempo_restante_b2_seg = max(0, tiempo_restante_seg)
    sesion.estado = EstadoSimulacro.completado
    sesion.completada_en = datetime.utcnow()
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def obtener_resultado(
    db: AsyncSession, sesion_id: int, usuario_id: int
) -> dict:
    sesion = await _get_sesion(db, sesion_id, usuario_id)

    ids = json.loads(sesion.preguntas_ids)
    respuestas = json.loads(sesion.respuestas)  # {str(pregunta_id): opcion_id}

    if not ids:
        return {"total": 0, "respondidas": 0, "correctas": 0, "porcentaje": 0, "por_materia": []}

    # Obtener opción correcta y materia para cada pregunta
    res = await db.execute(
        select(
            Pregunta.id,
            Materia.nombre,
            Materia.codigo_icfes,
            Respuesta.id.label("opcion_correcta_id"),
        )
        .join(Respuesta, and_(
            Respuesta.pregunta_id == Pregunta.id,
            Respuesta.es_correcta == True,
        ))
        .join(Materia, Pregunta.materia_id == Materia.id)
        .where(Pregunta.id.in_(ids))
    )
    filas = res.all()

    stats: dict[str, dict] = {}
    for pid, materia_nombre, codigo, opcion_correcta_id in filas:
        if materia_nombre not in stats:
            stats[materia_nombre] = {"total": 0, "correctas": 0, "codigo": codigo}
        stats[materia_nombre]["total"] += 1
        elegida = respuestas.get(str(pid))
        if elegida is not None and int(elegida) == opcion_correcta_id:
            stats[materia_nombre]["correctas"] += 1

    total_correctas = sum(v["correctas"] for v in stats.values())
    total = len(ids)

    return {
        "sesion_id": sesion_id,
        "total": total,
        "respondidas": len(respuestas),
        "correctas": total_correctas,
        "porcentaje": round(total_correctas / total * 100, 1) if total > 0 else 0,
        "por_materia": [
            {
                "materia": k,
                "codigo": v["codigo"],
                "total": v["total"],
                "correctas": v["correctas"],
                "porcentaje": round(v["correctas"] / v["total"] * 100, 1) if v["total"] > 0 else 0,
            }
            for k, v in stats.items()
        ],
        "tiempo_usado_b1_seg": 10800 - sesion.tiempo_restante_b1_seg,
        "tiempo_usado_b2_seg": 10800 - sesion.tiempo_restante_b2_seg,
        "completada_en": sesion.completada_en.isoformat() if sesion.completada_en else None,
    }


async def _get_sesion(
    db: AsyncSession, sesion_id: int, usuario_id: int
) -> SimulacroSesion:
    from fastapi import HTTPException
    res = await db.execute(
        select(SimulacroSesion).where(
            SimulacroSesion.id == sesion_id,
            SimulacroSesion.usuario_id == usuario_id,
        )
    )
    sesion = res.scalar_one_or_none()
    if not sesion:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    return sesion
