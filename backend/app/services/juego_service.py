"""
app/services/juego_service.py
Lógica de negocio para el modo libre de juego.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contenido import Materia, Pregunta, Respuesta, Pista
from app.models.juego import (
    SesionJuego,
    RespuestaUsuario,
    EstadisticaUsuario,
    ModoJuego,
)
from app.schemas.juego import IniciarSesionRequest, ResponderPreguntaRequest


class JuegoError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


# ─── Materias ─────────────────────────────────────────────────────────────────


async def obtener_materias(db: AsyncSession) -> list[Materia]:
    resultado = await db.execute(
        select(Materia).where(Materia.esta_activa == True).order_by(Materia.id)
    )
    return resultado.scalars().all()


# ─── Preparar pregunta con respuestas en orden aleatorio ──────────────────────


def preparar_pregunta(pregunta: Pregunta) -> dict:
    letras = ["A", "B", "C", "D"]
    opciones = list(pregunta.respuestas)
    random.shuffle(opciones)

    return {
        "id": pregunta.id,
        "enunciado": pregunta.enunciado,
        "imagen_url": pregunta.imagen_url,
        "tipo": pregunta.tipo,
        "nivel_dificultad": pregunta.nivel_dificultad,
        "opciones": [
            {"id": r.id, "letra": letras[i], "texto": r.texto}
            for i, r in enumerate(opciones)
        ],
    }


# ─── Preguntas ────────────────────────────────────────────────────────────────


async def obtener_preguntas_aleatorias(
    db: AsyncSession,
    materia_ids: list[int],
    cantidad: int = 10,
    excluir_ids: list[int] = [],
) -> list[dict]:
    query = (
        select(Pregunta)
        .options(selectinload(Pregunta.respuestas))
        .where(
            Pregunta.materia_id.in_(materia_ids),
            Pregunta.esta_activa == True,
        )
        .order_by(func.random())
        .limit(cantidad)
    )

    if excluir_ids:
        query = query.where(Pregunta.id.notin_(excluir_ids))

    resultado = await db.execute(query)
    preguntas = resultado.scalars().all()

    return [preparar_pregunta(p) for p in preguntas]


# ─── Sesión ───────────────────────────────────────────────────────────────────


async def iniciar_sesion(
    db: AsyncSession,
    usuario_id: int,
    datos: IniciarSesionRequest,
) -> SesionJuego:
    resultado = await db.execute(
        select(Materia).where(Materia.id.in_(datos.materia_ids))
    )
    materias = resultado.scalars().all()
    if not materias:
        raise JuegoError("No se encontraron las materias seleccionadas", 404)

    sesion = SesionJuego(
        usuario_id=usuario_id,
        modo_juego=datos.modo_juego,
        total_preguntas=datos.total_preguntas,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def responder_pregunta(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    datos: ResponderPreguntaRequest,
) -> dict:
    resultado = await db.execute(
        select(SesionJuego).where(
            SesionJuego.id == sesion_id,
            SesionJuego.usuario_id == usuario_id,
            SesionJuego.completada == False,
        )
    )
    sesion = resultado.scalar_one_or_none()
    if not sesion:
        raise JuegoError("Sesión no encontrada o ya finalizada", 404)

    resultado = await db.execute(
        select(Pregunta)
        .options(selectinload(Pregunta.respuestas), selectinload(Pregunta.pistas))
        .where(Pregunta.id == datos.pregunta_id)
    )
    pregunta = resultado.scalar_one_or_none()
    if not pregunta:
        raise JuegoError("Pregunta no encontrada", 404)

    opcion_elegida = next(
        (r for r in pregunta.respuestas if r.id == datos.opcion_id), None
    )
    if not opcion_elegida:
        raise JuegoError("Opción no válida para esta pregunta", 400)

    es_correcta = opcion_elegida.es_correcta
    opcion_correcta = next(r for r in pregunta.respuestas if r.es_correcta)

    respuesta = RespuestaUsuario(
        sesion_id=sesion_id,
        pregunta_id=datos.pregunta_id,
        opcion_elegida_id=datos.opcion_id,
        es_correcta=es_correcta,
        uso_pista=datos.uso_pista,
        tiempo_respuesta_ms=datos.tiempo_respuesta_ms,
    )
    db.add(respuesta)

    sesion.total_correctas = (sesion.total_correctas or 0) + (1 if es_correcta else 0)
    if datos.uso_pista:
        sesion.pistas_usadas = (sesion.pistas_usadas or 0) + 1

    pregunta.veces_respondida += 1
    if not es_correcta:
        pregunta.veces_incorrecta += 1

    await db.commit()

    return {
        "es_correcta": es_correcta,
        "opcion_correcta_id": opcion_correcta.id,
        "explicacion": pregunta.explicacion_texto,
        "pista_disponible": len(pregunta.pistas) > 0,
    }


async def finalizar_sesion(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
) -> SesionJuego:
    resultado = await db.execute(
        select(SesionJuego).where(
            SesionJuego.id == sesion_id,
            SesionJuego.usuario_id == usuario_id,
            SesionJuego.completada == False,
        )
    )
    sesion = resultado.scalar_one_or_none()
    if not sesion:
        raise JuegoError("Sesión no encontrada o ya finalizada", 404)

    ahora = datetime.utcnow()
    duracion = int((ahora - sesion.iniciada_en).total_seconds())

    puntaje = (sesion.total_correctas * 10) - (sesion.pistas_usadas * 2)
    puntaje = max(0, puntaje)

    sesion.completada = True
    sesion.finalizada_en = ahora
    sesion.duracion_segundos = duracion
    sesion.puntaje_obtenido = puntaje

    # ── Cargar usuario ────────────────────────────────────────────────────────
    from app.models.usuario import Usuario
    resultado_usuario = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado_usuario.scalar_one_or_none()

    if usuario:
        usuario.puntos_totales += puntaje

        # ── Lógica de rachas basada en sesiones completadas ───────────────────
        hoy = ahora.date()

        # Buscar la última sesión completada antes de la actual
        res_ultima = await db.execute(
            select(SesionJuego)
            .where(
                SesionJuego.usuario_id == usuario_id,
                SesionJuego.completada == True,
                SesionJuego.id != sesion_id,
            )
            .order_by(SesionJuego.finalizada_en.desc())
            .limit(1)
        )
        ultima_sesion = res_ultima.scalar_one_or_none()

        if ultima_sesion is None:
            # Primera sesión completada
            usuario.racha_actual = 1
        else:
            ultimo_dia = ultima_sesion.finalizada_en.date()

            if ultimo_dia == hoy:
                # Ya completó una sesión hoy — racha no cambia
                pass
            elif ultimo_dia == hoy - timedelta(days=1):
                # Completó una sesión ayer — racha sube
                usuario.racha_actual += 1
            else:
                # Pasaron más de un día sin jugar — racha se rompe
                usuario.racha_actual = 1

        # Actualizar racha máxima si fue superada
        if usuario.racha_actual > usuario.racha_maxima:
            usuario.racha_maxima = usuario.racha_actual

    # ── Actualizar estadísticas por materia ───────────────────────────────────
    res_stats = await db.execute(
        select(
            Pregunta.materia_id,
            func.count().label("total"),
            func.sum(case((RespuestaUsuario.es_correcta == True, 1), else_=0)).label("correctas"),
        )
        .join(Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id)
        .where(RespuestaUsuario.sesion_id == sesion_id)
        .group_by(Pregunta.materia_id)
    )
    filas = res_stats.all()

    for fila in filas:
        materia_id = fila.materia_id
        total_sesion = fila.total
        correctas_sesion = int(fila.correctas or 0)

        res_est = await db.execute(
            select(EstadisticaUsuario).where(
                EstadisticaUsuario.usuario_id == usuario_id,
                EstadisticaUsuario.materia_id == materia_id,
            )
        )
        estadistica = res_est.scalar_one_or_none()

        if estadistica:
            estadistica.total_respondidas += total_sesion
            estadistica.total_correctas += correctas_sesion
            estadistica.porcentaje_acierto = round(
                estadistica.total_correctas / estadistica.total_respondidas * 100, 1
            )
            estadistica.ultima_sesion = ahora
        else:
            db.add(EstadisticaUsuario(
                usuario_id=usuario_id,
                materia_id=materia_id,
                total_respondidas=total_sesion,
                total_correctas=correctas_sesion,
                porcentaje_acierto=round(correctas_sesion / total_sesion * 100, 1),
                ultima_sesion=ahora,
            ))

    await db.commit()
    await db.refresh(sesion)
    return sesion