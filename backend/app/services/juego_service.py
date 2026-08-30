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
from app.services import online_state
from app.utils.tiempo import utc_a_bogota


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
            {
                "id": r.id,
                "letra": letras[i],
                "texto": r.texto,
                "imagen_url": r.imagen_url,
            }
            for i, r in enumerate(opciones)
        ],
    }


# ─── Preguntas ────────────────────────────────────────────────────────────────


async def obtener_preguntas_aleatorias(
    db: AsyncSession,
    materia_ids: list[int],
    cantidad: int = 10,
    excluir_ids: list[int] = [],
    usuario_id: int | None = None,
) -> list[dict]:
    # Excluir las últimas 30 preguntas respondidas por el usuario en estas materias
    recientes: list[int] = []
    if usuario_id:
        res = await db.execute(
            select(RespuestaUsuario.pregunta_id)
            .join(SesionJuego, RespuestaUsuario.sesion_id == SesionJuego.id)
            .join(Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id)
            .where(
                SesionJuego.usuario_id == usuario_id,
                Pregunta.materia_id.in_(materia_ids),
            )
            .order_by(RespuestaUsuario.respondida_en.desc())
            .limit(30)
        )
        recientes = [r[0] for r in res.all()]

    todos_excluir = list(set(excluir_ids + recientes))

    def _query(excluir: list[int]):
        q = (
            select(Pregunta)
            .options(selectinload(Pregunta.respuestas))
            .where(
                Pregunta.materia_id.in_(materia_ids),
                Pregunta.esta_activa == True,
            )
            .order_by(func.random())
            .limit(cantidad)
        )
        if excluir:
            q = q.where(Pregunta.id.notin_(excluir))
        return q

    resultado = await db.execute(_query(todos_excluir))
    preguntas = resultado.scalars().all()

    # Fallback: si no hay suficientes ignorando el historial, usar solo excluir_ids de sesión
    if not preguntas:
        resultado = await db.execute(_query(excluir_ids))
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

    # Idempotencia: si este intento concreto (checkpoint) ya fue procesado
    # (doble clic, reintento de red), se devuelve el resultado ya guardado
    # en vez de contarlo de nuevo. No cuenta puntos online de nuevo — esos
    # ya se acreditaron la primera vez. No aplica si el llamador no manda
    # checkpoint (ej. el poder 75%, que responde internamente una sola vez).
    if datos.checkpoint is not None:
        existe = await db.execute(
            select(RespuestaUsuario).where(
                RespuestaUsuario.sesion_id == sesion_id,
                RespuestaUsuario.checkpoint == datos.checkpoint,
            )
        )
        previa = existe.scalar_one_or_none()
        if previa:
            resultado_p = await db.execute(
                select(Pregunta)
                .options(selectinload(Pregunta.respuestas), selectinload(Pregunta.pistas))
                .where(Pregunta.id == previa.pregunta_id)
            )
            pregunta_previa = resultado_p.scalar_one_or_none()
            opcion_correcta_previa = (
                next((r for r in pregunta_previa.respuestas if r.es_correcta), None)
                if pregunta_previa
                else None
            )
            return {
                "es_correcta": previa.es_correcta,
                "opcion_correcta_id": (
                    opcion_correcta_previa.id
                    if opcion_correcta_previa
                    else previa.opcion_elegida_id
                ),
                "opcion_elegida_id": previa.opcion_elegida_id,
                "explicacion": pregunta_previa.explicacion_texto if pregunta_previa else None,
                "pista_disponible": bool(pregunta_previa.pistas) if pregunta_previa else False,
                "puntos_online": 0,
                "proteccion_usada": False,
            }

    if online_state.efecto_activo(usuario_id, "congelar"):
        raise JuegoError("Estás congelado por el rival, espera unos segundos", 403)

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
        checkpoint=datos.checkpoint,
    )
    db.add(respuesta)

    sesion.total_correctas = (sesion.total_correctas or 0) + (1 if es_correcta else 0)
    if datos.uso_pista:
        sesion.pistas_usadas = (sesion.pistas_usadas or 0) + 1

    pregunta.veces_respondida += 1
    if not es_correcta:
        pregunta.veces_incorrecta += 1

    await db.commit()

    puntos_online, proteccion_usada = online_state.puntos_por_respuesta(usuario_id, es_correcta)

    return {
        "es_correcta": es_correcta,
        "opcion_correcta_id": opcion_correcta.id,
        "opcion_elegida_id": datos.opcion_id,
        "explicacion": pregunta.explicacion_texto,
        "pista_disponible": len(pregunta.pistas) > 0,
        "puntos_online": puntos_online,
        "proteccion_usada": proteccion_usada,
    }


# ─── Minijuego (modo Arcade) ────────────────────────────────────────────────────

PUNTOS_POR_RONDA_MINIJUEGO = 2


async def registrar_bonus_minijuego(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    checkpoint: int,
) -> int:
    """Acredita los puntos de una ronda ganada del minijuego de Arcade.
    El monto lo decide el servidor (PUNTOS_POR_RONDA_MINIJUEGO), nunca el
    cliente. Idempotente: si el checkpoint ya fue procesado o es menor al
    ultimo registrado (doble clic, reintento de red, reconexion), se ignora
    y se devuelve el bonus acumulado sin sumar de nuevo.
    """
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

    if checkpoint > sesion.ultimo_bonus_checkpoint:
        sesion.puntos_bonus += PUNTOS_POR_RONDA_MINIJUEGO
        sesion.ultimo_bonus_checkpoint = checkpoint
        await db.commit()

    return sesion.puntos_bonus


# ─── Poderes (modo Online) ─────────────────────────────────────────────────────


async def usar_mitad_mitad(
    db: AsyncSession,
    usuario_id: int,
    pregunta_id: int,
) -> list[int]:
    """Devuelve hasta 2 ids de opciones incorrectas para ocultar. Consume el poder."""
    resultado = await db.execute(
        select(Pregunta)
        .options(selectinload(Pregunta.respuestas))
        .where(Pregunta.id == pregunta_id)
    )
    pregunta = resultado.scalar_one_or_none()
    if not pregunta:
        raise JuegoError("Pregunta no encontrada", 404)

    if not online_state.consumir_poder(usuario_id, "mitad_mitad"):
        raise JuegoError("No posees el poder mitad y mitad", 403)

    incorrectas = [r.id for r in pregunta.respuestas if not r.es_correcta]
    return random.sample(incorrectas, min(2, len(incorrectas)))


async def usar_setenta_cinco(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    pregunta_id: int,
) -> dict:
    """Elige una opción con 75% de probabilidad de ser la correcta y la responde
    a través del flujo normal de responder_pregunta. Consume el poder."""
    resultado = await db.execute(
        select(Pregunta)
        .options(selectinload(Pregunta.respuestas))
        .where(Pregunta.id == pregunta_id)
    )
    pregunta = resultado.scalar_one_or_none()
    if not pregunta:
        raise JuegoError("Pregunta no encontrada", 404)

    correcta = next((r for r in pregunta.respuestas if r.es_correcta), None)
    incorrectas = [r for r in pregunta.respuestas if not r.es_correcta]
    if not correcta and not incorrectas:
        raise JuegoError("La pregunta no tiene opciones válidas", 500)

    if not online_state.consumir_poder(usuario_id, "setenta_cinco"):
        raise JuegoError("No posees el poder 75%", 403)

    if correcta and (random.random() < 0.75 or not incorrectas):
        elegido_id = correcta.id
    else:
        elegido_id = random.choice(incorrectas).id

    datos = ResponderPreguntaRequest(pregunta_id=pregunta_id, opcion_id=elegido_id)
    return await responder_pregunta(db, sesion_id, usuario_id, datos)

async def finalizar_sesion(
    db: AsyncSession,
    sesion_id: int,
    usuario_id: int,
    puntaje_override: int | None = None,
) -> SesionJuego:
    """Cierra una sesión y liquida sus puntos.

    - Si `puntaje_override` viene informado (modo Online: el servidor ya
      calculó el puntaje real de la partida, con x2/protección incluidos),
      se usa tal cual — no se recalcula nada.
    - Si no, se usa la fórmula estándar (preguntas - pistas). En Arcade,
      además se suma `puntos_bonus` del minijuego, pero solo si la sesión
      tuvo 3 o más respuestas incorrectas (llegó a Game Over de verdad, no
      salida voluntaria antes) — verificado contando RespuestaUsuario, sin
      confiar en lo que diga el cliente.
    """
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

    puntos_preguntas = max(
        0, (sesion.total_correctas * 10) - (sesion.pistas_usadas * 2)
    )
    bonus_incluido = 0

    if puntaje_override is not None:
        puntaje = max(0, puntaje_override)
    else:
        puntaje = puntos_preguntas
        if sesion.modo_juego == ModoJuego.arcade and sesion.puntos_bonus > 0:
            resultado_incorrectas = await db.execute(
                select(func.count())
                .select_from(RespuestaUsuario)
                .where(
                    RespuestaUsuario.sesion_id == sesion_id,
                    RespuestaUsuario.es_correcta == False,
                )
            )
            total_incorrectas = resultado_incorrectas.scalar_one()
            if total_incorrectas >= 3:
                bonus_incluido = sesion.puntos_bonus
                puntaje += bonus_incluido

    # Atributos transitorios (no persisten) — para que el endpoint arme el
    # desglose sin tener que recalcularlo.
    sesion._puntos_preguntas = puntos_preguntas
    sesion._puntos_bonus_incluido = bonus_incluido

    sesion.completada = True
    sesion.finalizada_en = ahora
    sesion.duracion_segundos = duracion
    sesion.puntaje_obtenido = puntaje

    from app.models.usuario import Usuario

    resultado_usuario = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = resultado_usuario.scalar_one_or_none()

    if usuario:
        usuario.puntos_totales += puntaje

        # La racha se cuenta por día calendario en Bogotá, no en UTC — si no,
        # a estudiantes que juegan de noche (después de las 7pm) se les
        # desfasa el día y la racha se rompe o se infla sin motivo.
        hoy = utc_a_bogota(ahora).date()
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
            usuario.racha_actual = 1
        else:
            ultimo_dia = utc_a_bogota(ultima_sesion.finalizada_en).date()
            if ultimo_dia == hoy:
                pass
            elif ultimo_dia == hoy - timedelta(days=1):
                usuario.racha_actual += 1
            else:
                usuario.racha_actual = 1

        if usuario.racha_actual > usuario.racha_maxima:
            usuario.racha_maxima = usuario.racha_actual

    res_stats = await db.execute(
        select(
            Pregunta.materia_id,
            func.count().label("total"),
            func.sum(case((RespuestaUsuario.es_correcta == True, 1), else_=0)).label(
                "correctas"
            ),
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
            db.add(
                EstadisticaUsuario(
                    usuario_id=usuario_id,
                    materia_id=materia_id,
                    total_respondidas=total_sesion,
                    total_correctas=correctas_sesion,
                    porcentaje_acierto=round(correctas_sesion / total_sesion * 100, 1),
                    ultima_sesion=ahora,
                )
            )

    await db.commit()
    await db.refresh(sesion)
    return sesion
