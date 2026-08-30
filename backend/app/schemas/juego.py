"""
app/schemas/juego.py
Schemas para el modo libre: materias, preguntas y sesiones.
"""

from datetime import datetime
from pydantic import BaseModel
from app.models.contenido import TipoPregunta, NivelDificultad
from app.models.juego import ModoJuego


# ─── Materias ─────────────────────────────────────────────────────────────────


class MateriaRespuesta(BaseModel):
    id: int
    nombre: str
    codigo_icfes: str
    descripcion: str | None
    color_hex: str | None

    model_config = {"from_attributes": True}


# ─── Preguntas ────────────────────────────────────────────────────────────────


class OpcionSchema(BaseModel):
    """Opción con letra asignada dinámicamente. No incluye es_correcta."""

    id: int
    letra: str
    texto: str
    imagen_url: str | None = None
    model_config = {"from_attributes": True}


class PreguntaRespuesta(BaseModel):
    id: int
    enunciado: str
    imagen_url: str | None
    tipo: TipoPregunta
    nivel_dificultad: NivelDificultad
    opciones: list[OpcionSchema]
    texto_titulo: str | None = None
    texto_contenido: str | None = None

    model_config = {"from_attributes": True}


class RetroalimentacionRespuesta(BaseModel):
    """Respuesta devuelta después de que el usuario elige una opción."""

    es_correcta: bool
    opcion_correcta_id: int  # Frontend colorea en verde la opción con este id
    opcion_elegida_id: int  # Cuál opción se respondió (útil cuando la elige el poder 75%)
    explicacion: str | None
    pista_disponible: bool
    puntos_online: int = 0  # Puntos ganados para la partida online (0 fuera de online)
    proteccion_usada: bool = False  # True si el poder "equivocarse" absorbió este error


# ─── Sesión de juego ──────────────────────────────────────────────────────────


class IniciarSesionRequest(BaseModel):
    modo_juego: ModoJuego
    materia_ids: list[int]  # Materias seleccionadas por el usuario
    total_preguntas: int = 10  # Cuántas preguntas quiere responder


class ResponderPreguntaRequest(BaseModel):
    pregunta_id: int
    opcion_id: int  # La opción que eligió el usuario
    tiempo_respuesta_ms: int | None = None
    uso_pista: bool = False
    # Identificador único de este intento concreto (ej. índice de pregunta
    # dentro de la partida). Si se repite (doble clic, reintento de red),
    # el servidor devuelve el mismo resultado en vez de contar la respuesta
    # dos veces. Opcional para no romper otros llamadores (ej. poder 75%).
    checkpoint: int | None = None


class SesionRespuesta(BaseModel):
    sesion_id: int
    modo_juego: ModoJuego
    total_preguntas: int
    mensaje: str = "Sesión iniciada correctamente"

    model_config = {"from_attributes": True}


# ─── Poderes (modo Online) ─────────────────────────────────────────────────────


class MitadMitadRequest(BaseModel):
    pregunta_id: int


class MitadMitadRespuesta(BaseModel):
    ocultar_ids: list[int]  # Ids de opciones incorrectas a ocultar en el frontend


class SetentaCincoRequest(BaseModel):
    pregunta_id: int


# ─── Minijuego (modo Arcade) ────────────────────────────────────────────────────


class BonusMinijuegoRequest(BaseModel):
    checkpoint: int  # Identificador creciente de la ronda ganada (idempotencia)


class BonusMinijuegoRespuesta(BaseModel):
    puntos_bonus: int  # Total acumulado de bonus en la sesión hasta ahora


class ResultadoSesion(BaseModel):
    """Resumen al finalizar una sesión."""

    sesion_id: int
    modo_juego: ModoJuego
    total_preguntas: int
    total_correctas: int
    puntaje_obtenido: int
    puntos_preguntas: int = 0  # Desglose: parte del puntaje que viene de preguntas
    puntos_bonus: int = 0  # Desglose: parte del puntaje que viene del minijuego
    porcentaje_acierto: float
    pistas_usadas: int
    duracion_segundos: int | None
    mensaje: str

    model_config = {"from_attributes": True}
