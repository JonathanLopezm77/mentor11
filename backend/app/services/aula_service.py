"""
app/services/aula_service.py
Lógica de negocio para aulas, tareas y rankings del profesor.
"""

import random
import string
from datetime import datetime

from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aula import Aula, AulaEstudiante, Tarea, TareaProgreso
from app.models.contenido import Materia, Pregunta, Respuesta
from app.models.juego import SesionJuego, RespuestaUsuario, EstadisticaUsuario, ModoJuego
from app.models.usuario import Usuario, Avatar
from app.services.juego_service import preparar_pregunta


class AulaError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


# ── Utilidades ────────────────────────────────────────────────────────────────

def _generar_codigo(longitud: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))


async def _codigo_unico(db: AsyncSession) -> str:
    for _ in range(10):
        codigo = _generar_codigo()
        existe = await db.execute(select(Aula).where(Aula.codigo_acceso == codigo))
        if not existe.scalar_one_or_none():
            return codigo
    raise AulaError("No se pudo generar un código único. Inténtalo de nuevo.", 500)


# ── Crear aula ────────────────────────────────────────────────────────────────

async def crear_aula(db: AsyncSession, profesor_id: int, nombre: str, materia_id: int) -> Aula:
    res_mat = await db.execute(select(Materia).where(Materia.id == materia_id))
    if not res_mat.scalar_one_or_none():
        raise AulaError("Materia no encontrada", 404)

    codigo = await _codigo_unico(db)
    aula = Aula(
        profesor_id=profesor_id,
        nombre=nombre,
        materia_id=materia_id,
        codigo_acceso=codigo,
        esta_activa=True,
    )
    db.add(aula)
    await db.commit()
    await db.refresh(aula)
    return aula


# ── Listar aulas del profesor ─────────────────────────────────────────────────

async def listar_aulas_profesor(db: AsyncSession, profesor_id: int) -> list[dict]:
    res = await db.execute(
        select(Aula)
        .options(selectinload(Aula.materia), selectinload(Aula.estudiantes))
        .where(Aula.profesor_id == profesor_id, Aula.esta_activa == True)
        .order_by(Aula.creada_en.desc())
    )
    aulas = res.scalars().all()

    resultado = []
    for a in aulas:
        resultado.append({
            "id": a.id,
            "nombre": a.nombre,
            "codigo_acceso": a.codigo_acceso,
            "materia_id": a.materia_id,
            "materia_nombre": a.materia.nombre if a.materia else None,
            "profesor_nombre": "",
            "esta_activa": a.esta_activa,
            "creada_en": a.creada_en,
            "total_estudiantes": len([e for e in a.estudiantes if e.esta_activo]),
        })
    return resultado


# ── Detalle de aula ───────────────────────────────────────────────────────────

async def detalle_aula(db: AsyncSession, aula_id: int, profesor_id: int) -> dict:
    res = await db.execute(
        select(Aula)
        .options(
            selectinload(Aula.materia),
            selectinload(Aula.estudiantes).selectinload(AulaEstudiante.estudiante).selectinload(Usuario.avatar),
            selectinload(Aula.tareas).selectinload(Tarea.progresos),
        )
        .where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    aula = res.scalar_one_or_none()
    if not aula:
        raise AulaError("Aula no encontrada", 404)

    estudiantes_activos = [e for e in aula.estudiantes if e.esta_activo]
    total_est = len(estudiantes_activos)

    lista_est = []
    for ae in estudiantes_activos:
        est = ae.estudiante
        tareas_completadas = sum(
            1 for t in aula.tareas
            for p in t.progresos
            if p.estudiante_id == est.id and p.completada
        )
        lista_est.append({
            "id": est.id,
            "username": est.username,
            "avatar": est.avatar.imagen_src if est.avatar else None,
            "tareas_completadas": tareas_completadas,
            "total_tareas": len(aula.tareas),
            "en_seguimiento": ae.en_seguimiento,
        })

    lista_tareas = []
    for t in sorted(aula.tareas, key=lambda x: x.creada_en, reverse=True):
        completadas = sum(1 for p in t.progresos if p.completada)
        lista_tareas.append({
            "id": t.id,
            "aula_id": t.aula_id,
            "cantidad_preguntas": t.cantidad_preguntas,
            "creada_en": t.creada_en,
            "completada_por": completadas,
            "total_estudiantes": total_est,
        })

    return {
        "id": aula.id,
        "nombre": aula.nombre,
        "codigo_acceso": aula.codigo_acceso,
        "materia_id": aula.materia_id,
        "materia_nombre": aula.materia.nombre if aula.materia else None,
        "creada_en": aula.creada_en,
        "total_estudiantes": total_est,
        "estudiantes": lista_est,
        "tareas": lista_tareas,
    }


# ── Ranking del aula ──────────────────────────────────────────────────────────

async def ranking_aula(db: AsyncSession, aula_id: int, profesor_id: int) -> dict:
    res_aula = await db.execute(
        select(Aula)
        .options(selectinload(Aula.materia), selectinload(Aula.estudiantes))
        .where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    aula = res_aula.scalar_one_or_none()
    if not aula:
        raise AulaError("Aula no encontrada", 404)

    est_ids = [e.estudiante_id for e in aula.estudiantes if e.esta_activo]
    materia_id = aula.materia_id
    materia_nombre = aula.materia.nombre if aula.materia else "General"

    if not est_ids or not materia_id:
        return {"top": [], "bottom": [], "materia_nombre": materia_nombre}

    # Estadísticas de todos los estudiantes para la materia del aula
    res_stats = await db.execute(
        select(EstadisticaUsuario, Usuario, Avatar)
        .join(Usuario, EstadisticaUsuario.usuario_id == Usuario.id)
        .outerjoin(Avatar, Avatar.usuario_id == Usuario.id)
        .where(
            EstadisticaUsuario.usuario_id.in_(est_ids),
            EstadisticaUsuario.materia_id == materia_id,
        )
        .order_by(EstadisticaUsuario.porcentaje_acierto.desc())
    )
    filas = res_stats.all()

    entradas = []
    for i, (stat, usuario, avatar) in enumerate(filas):
        avatar_src = avatar.imagen_src if avatar else None
        entradas.append({
            "posicion": i + 1,
            "usuario_id": usuario.id,
            "username": usuario.username,
            "avatar": avatar_src,
            "porcentaje_acierto": float(stat.porcentaje_acierto),
            "total_respondidas": stat.total_respondidas,
        })

    top3 = entradas[:3]
    bottom3 = list(reversed(entradas[-3:])) if len(entradas) >= 3 else list(reversed(entradas))
    # Evitar duplicados si hay 3 o menos estudiantes
    if len(entradas) <= 3:
        bottom3 = []

    return {"top": top3, "bottom": bottom3, "materia_nombre": materia_nombre}


# ── Stats del grupo ───────────────────────────────────────────────────────────

async def stats_grupo(db: AsyncSession, aula_id: int, profesor_id: int) -> dict:
    res_aula = await db.execute(
        select(Aula)
        .options(selectinload(Aula.materia), selectinload(Aula.estudiantes), selectinload(Aula.tareas).selectinload(Tarea.progresos))
        .where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    aula = res_aula.scalar_one_or_none()
    if not aula:
        raise AulaError("Aula no encontrada", 404)

    est_ids = [e.estudiante_id for e in aula.estudiantes if e.esta_activo]
    total_est = len(est_ids)
    materia_id = aula.materia_id
    materia_nombre = aula.materia.nombre if aula.materia else "General"

    total_respondidas = 0
    suma_pct = 0.0
    con_stats = 0

    if est_ids and materia_id:
        res_stats = await db.execute(
            select(EstadisticaUsuario)
            .where(
                EstadisticaUsuario.usuario_id.in_(est_ids),
                EstadisticaUsuario.materia_id == materia_id,
            )
        )
        stats = res_stats.scalars().all()
        for s in stats:
            suma_pct += float(s.porcentaje_acierto)
            total_respondidas += s.total_respondidas
            con_stats += 1

    promedio = round(suma_pct / con_stats, 1) if con_stats else 0.0
    total_tareas = len(aula.tareas)
    tareas_completadas = sum(1 for t in aula.tareas for p in t.progresos if p.completada)

    return {
        "total_estudiantes": total_est,
        "promedio_acierto": promedio,
        "total_respondidas": total_respondidas,
        "total_tareas": total_tareas,
        "tareas_completadas_total": tareas_completadas,
        "materia_nombre": materia_nombre,
    }


# ── Stats individuales ────────────────────────────────────────────────────────

async def stats_estudiante(db: AsyncSession, aula_id: int, est_id: int, profesor_id: int) -> dict:
    res_aula = await db.execute(
        select(Aula)
        .options(selectinload(Aula.materia), selectinload(Aula.estudiantes), selectinload(Aula.tareas).selectinload(Tarea.progresos))
        .where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    aula = res_aula.scalar_one_or_none()
    if not aula:
        raise AulaError("Aula no encontrada", 404)

    es_miembro = any(e.estudiante_id == est_id and e.esta_activo for e in aula.estudiantes)
    if not es_miembro:
        raise AulaError("El estudiante no está en este aula", 404)

    res_usuario = await db.execute(
        select(Usuario).options(selectinload(Usuario.avatar)).where(Usuario.id == est_id)
    )
    usuario = res_usuario.scalar_one_or_none()
    if not usuario:
        raise AulaError("Estudiante no encontrado", 404)

    materia_id = aula.materia_id
    porcentaje = 0.0
    total_respondidas = 0
    total_correctas = 0

    if materia_id:
        res_stat = await db.execute(
            select(EstadisticaUsuario).where(
                EstadisticaUsuario.usuario_id == est_id,
                EstadisticaUsuario.materia_id == materia_id,
            )
        )
        stat = res_stat.scalar_one_or_none()
        if stat:
            porcentaje = float(stat.porcentaje_acierto)
            total_respondidas = stat.total_respondidas
            total_correctas = stat.total_correctas

    total_tareas = len(aula.tareas)
    tareas_completadas = sum(
        1 for t in aula.tareas
        for p in t.progresos
        if p.estudiante_id == est_id and p.completada
    )

    avatar_src = usuario.avatar.imagen_src if usuario.avatar else None

    return {
        "usuario_id": usuario.id,
        "username": usuario.username,
        "avatar": avatar_src,
        "porcentaje_acierto": porcentaje,
        "total_respondidas": total_respondidas,
        "total_correctas": total_correctas,
        "tareas_completadas": tareas_completadas,
        "total_tareas": total_tareas,
    }


# ── Marcar / desmarcar seguimiento ───────────────────────────────────────────

async def marcar_seguimiento(db: AsyncSession, aula_id: int, est_id: int, profesor_id: int, marcar: bool) -> dict:
    # Verificar que el aula pertenece al profesor
    res_aula = await db.execute(
        select(Aula).where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    if not res_aula.scalar_one_or_none():
        raise AulaError("Aula no encontrada", 404)

    res_ae = await db.execute(
        select(AulaEstudiante).where(
            AulaEstudiante.aula_id == aula_id,
            AulaEstudiante.estudiante_id == est_id,
            AulaEstudiante.esta_activo == True,
        )
    )
    ae = res_ae.scalar_one_or_none()
    if not ae:
        raise AulaError("Estudiante no encontrado en el aula", 404)

    ae.en_seguimiento = marcar
    await db.commit()
    return {"en_seguimiento": marcar}


async def listar_seguimientos_profesor(db: AsyncSession, profesor_id: int) -> list[dict]:
    """Devuelve todos los estudiantes marcados en cualquier aula del profesor."""
    res = await db.execute(
        select(AulaEstudiante, Aula, Usuario, Avatar, EstadisticaUsuario)
        .join(Aula, AulaEstudiante.aula_id == Aula.id)
        .join(Usuario, AulaEstudiante.estudiante_id == Usuario.id)
        .outerjoin(Avatar, Avatar.usuario_id == Usuario.id)
        .outerjoin(
            EstadisticaUsuario,
            (EstadisticaUsuario.usuario_id == Usuario.id) &
            (EstadisticaUsuario.materia_id == Aula.materia_id)
        )
        .where(
            Aula.profesor_id == profesor_id,
            Aula.esta_activa == True,
            AulaEstudiante.en_seguimiento == True,
            AulaEstudiante.esta_activo == True,
        )
        .order_by(Aula.id, Usuario.username)
    )
    filas = res.all()

    # Agrupar tareas completadas por estudiante+aula
    resultado = []
    for ae, aula, usuario, avatar, stat in filas:
        # Contar tareas completadas para este estudiante en esta aula
        res_tareas = await db.execute(
            select(func.count()).select_from(TareaProgreso)
            .join(Tarea, TareaProgreso.tarea_id == Tarea.id)
            .where(
                Tarea.aula_id == aula.id,
                TareaProgreso.estudiante_id == usuario.id,
                TareaProgreso.completada == True,
            )
        )
        tareas_completadas = res_tareas.scalar() or 0

        res_total_tareas = await db.execute(
            select(func.count()).select_from(Tarea).where(Tarea.aula_id == aula.id)
        )
        total_tareas = res_total_tareas.scalar() or 0

        resultado.append({
            "aula_id": aula.id,
            "aula_nombre": aula.nombre,
            "materia_nombre": None,  # se carga abajo si hay materia
            "estudiante_id": usuario.id,
            "username": usuario.username,
            "avatar": avatar.imagen_src if avatar else None,
            "porcentaje_acierto": float(stat.porcentaje_acierto) if stat else 0.0,
            "total_respondidas": stat.total_respondidas if stat else 0,
            "tareas_completadas": tareas_completadas,
            "total_tareas": total_tareas,
        })

    # Cargar nombres de materias
    materia_ids = list({r["aula_id"] for r in resultado})
    if materia_ids:
        res_mat = await db.execute(
            select(Aula.id, Materia.nombre)
            .join(Materia, Aula.materia_id == Materia.id)
            .where(Aula.id.in_(materia_ids))
        )
        mapa = {aid: nombre for aid, nombre in res_mat.all()}
        for r in resultado:
            r["materia_nombre"] = mapa.get(r["aula_id"])

    return resultado


# ── Crear tarea ───────────────────────────────────────────────────────────────

async def crear_tarea(db: AsyncSession, aula_id: int, profesor_id: int, cantidad_preguntas: int) -> dict:
    res_aula = await db.execute(
        select(Aula).options(selectinload(Aula.estudiantes))
        .where(Aula.id == aula_id, Aula.profesor_id == profesor_id)
    )
    aula = res_aula.scalar_one_or_none()
    if not aula:
        raise AulaError("Aula no encontrada", 404)

    if cantidad_preguntas < 1 or cantidad_preguntas > 30:
        raise AulaError("La cantidad debe estar entre 1 y 30", 400)

    tarea = Tarea(aula_id=aula_id, cantidad_preguntas=cantidad_preguntas)
    db.add(tarea)
    await db.commit()
    await db.refresh(tarea)

    total_est = len([e for e in aula.estudiantes if e.esta_activo])

    return {
        "id": tarea.id,
        "aula_id": tarea.aula_id,
        "cantidad_preguntas": tarea.cantidad_preguntas,
        "creada_en": tarea.creada_en,
        "completada_por": 0,
        "total_estudiantes": total_est,
    }


# ── Unirse a un aula (estudiante) ─────────────────────────────────────────────

async def unirse_a_aula(db: AsyncSession, estudiante_id: int, codigo: str) -> dict:
    codigo = codigo.strip().upper()
    res = await db.execute(
        select(Aula)
        .options(selectinload(Aula.materia), selectinload(Aula.estudiantes))
        .where(Aula.codigo_acceso == codigo, Aula.esta_activa == True)
    )
    aula = res.scalar_one_or_none()
    if not aula:
        raise AulaError("Código inválido o aula inactiva", 404)

    ya_inscrito = any(e.estudiante_id == estudiante_id for e in aula.estudiantes)
    if ya_inscrito:
        # Reactivar si estaba inactivo
        ae = next((e for e in aula.estudiantes if e.estudiante_id == estudiante_id), None)
        if ae and not ae.esta_activo:
            ae.esta_activo = True
            await db.commit()
        return {"id": aula.id, "nombre": aula.nombre, "mensaje": "Ya estás inscrito en este aula"}

    ae = AulaEstudiante(aula_id=aula.id, estudiante_id=estudiante_id, esta_activo=True)
    db.add(ae)
    await db.commit()

    return {
        "id": aula.id,
        "nombre": aula.nombre,
        "materia_nombre": aula.materia.nombre if aula.materia else None,
        "mensaje": "Te uniste al aula correctamente",
    }


# ── Listar aulas del estudiante ───────────────────────────────────────────────

async def listar_aulas_estudiante(db: AsyncSession, estudiante_id: int) -> list[dict]:
    res = await db.execute(
        select(AulaEstudiante)
        .options(
            selectinload(AulaEstudiante.aula).selectinload(Aula.materia),
            selectinload(AulaEstudiante.aula).selectinload(Aula.tareas).selectinload(Tarea.progresos),
        )
        .where(AulaEstudiante.estudiante_id == estudiante_id, AulaEstudiante.esta_activo == True)
    )
    inscripciones = res.scalars().all()

    resultado = []
    for ae in inscripciones:
        a = ae.aula
        if not a.esta_activa:
            continue
        tareas_pendientes = []
        for t in a.tareas:
            progreso = next((p for p in t.progresos if p.estudiante_id == estudiante_id), None)
            if not progreso or not progreso.completada:
                tareas_pendientes.append({
                    "id": t.id,
                    "cantidad_preguntas": t.cantidad_preguntas,
                    "creada_en": t.creada_en,
                    "completada": False,
                    "sesion_id": progreso.sesion_id if progreso else None,
                })
            else:
                tareas_pendientes.append({
                    "id": t.id,
                    "cantidad_preguntas": t.cantidad_preguntas,
                    "creada_en": t.creada_en,
                    "completada": True,
                    "sesion_id": progreso.sesion_id if progreso else None,
                })
        resultado.append({
            "id": a.id,
            "nombre": a.nombre,
            "codigo_acceso": a.codigo_acceso,
            "materia_id": a.materia_id,
            "materia_nombre": a.materia.nombre if a.materia else None,
            "profesor_nombre": "",  # se podría cargar si se necesita
            "esta_activa": a.esta_activa,
            "creada_en": a.creada_en,
            "total_estudiantes": 0,
            "tareas": tareas_pendientes,
        })
    return resultado


# ── Iniciar tarea (estudiante) ────────────────────────────────────────────────

async def iniciar_tarea(db: AsyncSession, tarea_id: int, estudiante_id: int) -> dict:
    # Cargar tarea + aula + materia
    res = await db.execute(
        select(Tarea)
        .options(selectinload(Tarea.aula).selectinload(Aula.materia))
        .where(Tarea.id == tarea_id)
    )
    tarea = res.scalar_one_or_none()
    if not tarea:
        raise AulaError("Tarea no encontrada", 404)

    aula = tarea.aula
    materia_id = aula.materia_id
    if not materia_id:
        raise AulaError("El aula no tiene materia asignada", 400)

    # Verificar que el estudiante está en el aula
    res_ae = await db.execute(
        select(AulaEstudiante).where(
            AulaEstudiante.aula_id == aula.id,
            AulaEstudiante.estudiante_id == estudiante_id,
            AulaEstudiante.esta_activo == True,
        )
    )
    if not res_ae.scalar_one_or_none():
        raise AulaError("No estás inscrito en este aula", 403)

    # Revisar progreso existente
    res_prog = await db.execute(
        select(TareaProgreso).where(
            TareaProgreso.tarea_id == tarea_id,
            TareaProgreso.estudiante_id == estudiante_id,
        )
    )
    progreso = res_prog.scalar_one_or_none()

    if progreso and progreso.completada:
        raise AulaError("Ya completaste esta tarea", 400)

    if progreso and progreso.sesion_id:
        # Ya inició, devolver sesion existente + preguntas ya asignadas
        res_sesion = await db.execute(select(SesionJuego).where(SesionJuego.id == progreso.sesion_id))
        sesion = res_sesion.scalar_one_or_none()
        preguntas = await _preguntas_de_sesion(db, progreso.sesion_id)
        return {
            "sesion_id": progreso.sesion_id,
            "tarea_id": tarea_id,
            "materia_id": materia_id,
            "materia_nombre": aula.materia.nombre,
            "cantidad_preguntas": tarea.cantidad_preguntas,
            "preguntas": preguntas,
            "ya_iniciada": True,
        }

    # Preguntas ya respondidas por el estudiante en tareas anteriores de ESTE aula
    preguntas_usadas = await _preguntas_usadas_en_aula(db, estudiante_id, aula.id)

    # Seleccionar preguntas nuevas
    from sqlalchemy.orm import selectinload as sil
    query = (
        select(Pregunta)
        .options(sil(Pregunta.respuestas))
        .where(
            Pregunta.materia_id == materia_id,
            Pregunta.esta_activa == True,
        )
        .order_by(func.random())
        .limit(tarea.cantidad_preguntas)
    )
    if preguntas_usadas:
        query = query.where(Pregunta.id.notin_(preguntas_usadas))

    res_p = await db.execute(query)
    preguntas_objs = res_p.scalars().all()

    if not preguntas_objs:
        raise AulaError("No hay preguntas disponibles para esta tarea", 404)

    # Crear sesión de juego
    sesion = SesionJuego(
        usuario_id=estudiante_id,
        modo_juego=ModoJuego.libre,
        total_preguntas=len(preguntas_objs),
    )
    db.add(sesion)
    await db.flush()

    # Crear/actualizar progreso
    ahora = datetime.utcnow()
    if progreso:
        progreso.sesion_id = sesion.id
        progreso.iniciada_en = ahora
    else:
        progreso = TareaProgreso(
            tarea_id=tarea_id,
            estudiante_id=estudiante_id,
            sesion_id=sesion.id,
            completada=False,
            iniciada_en=ahora,
        )
        db.add(progreso)

    await db.commit()
    await db.refresh(sesion)

    preguntas_preparadas = [preparar_pregunta(p) for p in preguntas_objs]

    return {
        "sesion_id": sesion.id,
        "tarea_id": tarea_id,
        "materia_id": materia_id,
        "materia_nombre": aula.materia.nombre,
        "cantidad_preguntas": len(preguntas_preparadas),
        "preguntas": preguntas_preparadas,
        "ya_iniciada": False,
    }


async def _preguntas_usadas_en_aula(db: AsyncSession, estudiante_id: int, aula_id: int) -> list[int]:
    """Devuelve IDs de preguntas ya respondidas en cualquier tarea de este aula."""
    res = await db.execute(
        select(RespuestaUsuario.pregunta_id)
        .join(SesionJuego, RespuestaUsuario.sesion_id == SesionJuego.id)
        .join(TareaProgreso, TareaProgreso.sesion_id == SesionJuego.id)
        .join(Tarea, TareaProgreso.tarea_id == Tarea.id)
        .where(
            TareaProgreso.estudiante_id == estudiante_id,
            Tarea.aula_id == aula_id,
        )
    )
    return [r[0] for r in res.all()]


async def _preguntas_de_sesion(db: AsyncSession, sesion_id: int) -> list[dict]:
    """Devuelve las preguntas ya asignadas a una sesión existente."""
    from sqlalchemy.orm import selectinload as sil
    res = await db.execute(
        select(RespuestaUsuario.pregunta_id)
        .where(RespuestaUsuario.sesion_id == sesion_id)
        .distinct()
    )
    ids = [r[0] for r in res.all()]
    if not ids:
        return []
    res_p = await db.execute(
        select(Pregunta).options(sil(Pregunta.respuestas)).where(Pregunta.id.in_(ids))
    )
    return [preparar_pregunta(p) for p in res_p.scalars().all()]


# ── Completar tarea (estudiante) ──────────────────────────────────────────────

async def completar_tarea(db: AsyncSession, tarea_id: int, estudiante_id: int) -> dict:
    res = await db.execute(
        select(TareaProgreso).where(
            TareaProgreso.tarea_id == tarea_id,
            TareaProgreso.estudiante_id == estudiante_id,
        )
    )
    progreso = res.scalar_one_or_none()
    if not progreso:
        raise AulaError("No has iniciado esta tarea", 400)
    if progreso.completada:
        return {"mensaje": "Tarea ya marcada como completada"}

    progreso.completada = True
    progreso.completada_en = datetime.utcnow()
    await db.commit()

    return {"mensaje": "Tarea completada correctamente"}
