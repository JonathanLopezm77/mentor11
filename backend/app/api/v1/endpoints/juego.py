"""
app/api/v1/endpoints/juego.py
Endpoints del modo libre de juego.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.juego import (
    MateriaRespuesta,
    PreguntaRespuesta,
    SesionRespuesta,
    IniciarSesionRequest,
    ResponderPreguntaRequest,
    RetroalimentacionRespuesta,
    ResultadoSesion,
    MitadMitadRequest,
    MitadMitadRespuesta,
    SetentaCincoRequest,
    BonusMinijuegoRequest,
    BonusMinijuegoRespuesta,
    OpcionSchema,  # noqa: F401
)
from app.services.juego_service import (
    obtener_materias,
    obtener_preguntas_aleatorias,
    iniciar_sesion,
    responder_pregunta,
    finalizar_sesion,
    usar_mitad_mitad,
    usar_setenta_cinco,
    registrar_bonus_minijuego,
    JuegoError,
)

router = APIRouter()


# ─── Materias ─────────────────────────────────────────────────────────────────


@router.get("/materias", response_model=list[MateriaRespuesta])
async def listar_materias(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Devuelve las 5 materias del ICFES.
    El frontend las muestra en la pantalla de selección del modo libre.
    """
    return await obtener_materias(db)


# ─── Preguntas ────────────────────────────────────────────────────────────────


@router.get("/preguntas", response_model=list[PreguntaRespuesta])
async def obtener_preguntas(
    materia_ids: str,           # Ej: "1,2,3" separado por comas
    cantidad: int = 10,
    excluir_ids: str = "",      # Ej: "5,12,30" — preguntas ya vistas (modo arcade)
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Devuelve preguntas aleatorias para las materias seleccionadas.
    Las opciones NO incluyen cuál es la correcta (eso lo revela /responder).
    excluir_ids permite al modo arcade evitar repetir preguntas ya vistas.
    """
    try:
        ids = [int(x) for x in materia_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="materia_ids debe ser una lista de números separados por comas",
        )

    excluir = []
    if excluir_ids:
        try:
            excluir = [int(x) for x in excluir_ids.split(",") if x]
        except ValueError:
            pass

    preguntas = await obtener_preguntas_aleatorias(db, ids, cantidad, excluir, usuario_id=usuario.id)
    if not preguntas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron preguntas para las materias seleccionadas",
        )

    return preguntas


# ─── Sesión ───────────────────────────────────────────────────────────────────


@router.post("/sesiones", response_model=SesionRespuesta, status_code=201)
async def crear_sesion(
    datos: IniciarSesionRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Inicia una nueva sesión de juego.
    El frontend llama esto cuando el estudiante presiona 'Comenzar'.
    """
    try:
        sesion = await iniciar_sesion(db, usuario.id, datos)
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {
        "sesion_id": sesion.id,
        "modo_juego": sesion.modo_juego,
        "total_preguntas": sesion.total_preguntas,
        "mensaje": "Sesión iniciada correctamente",
    }


@router.post(
    "/sesiones/{sesion_id}/responder", response_model=RetroalimentacionRespuesta
)
async def responder(
    sesion_id: int,
    datos: ResponderPreguntaRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Registra la respuesta del usuario y devuelve retroalimentación inmediata:
    si acertó, cuál era la correcta y la explicación pedagógica.
    """
    try:
        resultado = await responder_pregunta(db, sesion_id, usuario.id, datos)
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado


@router.post("/poderes/mitad_mitad", response_model=MitadMitadRespuesta)
async def poder_mitad_mitad(
    datos: MitadMitadRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Consume el poder 'mitad y mitad' y devuelve 2 opciones incorrectas a ocultar."""
    try:
        ocultar_ids = await usar_mitad_mitad(db, usuario.id, datos.pregunta_id)
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {"ocultar_ids": ocultar_ids}


@router.post(
    "/sesiones/{sesion_id}/poderes/setenta_cinco",
    response_model=RetroalimentacionRespuesta,
)
async def poder_setenta_cinco(
    sesion_id: int,
    datos: SetentaCincoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Consume el poder '75%' — el servidor elige la opción y la responde
    con 75% de probabilidad real de acertar."""
    try:
        resultado = await usar_setenta_cinco(db, sesion_id, usuario.id, datos.pregunta_id)
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return resultado


@router.post("/sesiones/{sesion_id}/poderes/bonus_minijuego", response_model=BonusMinijuegoRespuesta)
async def poder_bonus_minijuego(
    sesion_id: int,
    datos: BonusMinijuegoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Acredita los puntos de una ronda ganada del minijuego de Arcade.
    El servidor decide cuántos puntos vale (no el cliente); es idempotente
    ante reintentos gracias al checkpoint creciente."""
    try:
        puntos_bonus = await registrar_bonus_minijuego(
            db, sesion_id, usuario.id, datos.checkpoint
        )
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return {"puntos_bonus": puntos_bonus}


@router.post("/sesiones/{sesion_id}/finalizar", response_model=ResultadoSesion)
async def finalizar(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Finaliza la sesión y devuelve el resumen de resultados.
    El frontend llama esto cuando se acaban las preguntas.
    """
    try:
        sesion = await finalizar_sesion(db, sesion_id, usuario.id)
    except JuegoError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    total = sesion.total_preguntas or 1
    porcentaje = round((sesion.total_correctas / total) * 100, 1)

    return {
        "sesion_id": sesion.id,
        "modo_juego": sesion.modo_juego,
        "total_preguntas": sesion.total_preguntas,
        "total_correctas": sesion.total_correctas,
        "puntaje_obtenido": sesion.puntaje_obtenido,
        "puntos_preguntas": getattr(sesion, "_puntos_preguntas", sesion.puntaje_obtenido),
        "puntos_bonus": getattr(sesion, "_puntos_bonus_incluido", 0),
        "porcentaje_acierto": porcentaje,
        "pistas_usadas": sesion.pistas_usadas,
        "duracion_segundos": sesion.duracion_segundos,
        "mensaje": f"¡Obtuviste {porcentaje}% de acierto!",
    }
