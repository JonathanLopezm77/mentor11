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

    model_config = {"from_attributes": True}


class PreguntaRespuesta(BaseModel):
    id: int
    enunciado: str
    imagen_url: str | None
    tipo: TipoPregunta
    nivel_dificultad: NivelDificultad
    opciones: list[OpcionSchema]

    model_config = {"from_attributes": True}


class RetroalimentacionRespuesta(BaseModel):
    """Respuesta devuelta después de que el usuario elige una opción."""

    es_correcta: bool
    opcion_correcta_id: int   # Frontend colorea en verde la opción con este id
    explicacion: str | None
    pista_disponible: bool


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


class SesionRespuesta(BaseModel):
    sesion_id: int
    modo_juego: ModoJuego
    total_preguntas: int
    mensaje: str = "Sesión iniciada correctamente"

    model_config = {"from_attributes": True}


class ResultadoSesion(BaseModel):
    """Resumen al finalizar una sesión."""

    sesion_id: int
    modo_juego: ModoJuego
    total_preguntas: int
    total_correctas: int
    puntaje_obtenido: int
    porcentaje_acierto: float
    pistas_usadas: int
    duracion_segundos: int | None
    mensaje: str

    model_config = {"from_attributes": True}
