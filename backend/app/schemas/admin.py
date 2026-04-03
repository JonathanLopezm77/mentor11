"""
app/schemas/admin.py
Schemas Pydantic para el panel de administración de contenido.
"""
from pydantic import BaseModel
from app.models.contenido import TipoPregunta, NivelDificultad


# ─── Opciones ─────────────────────────────────────────────────────────────────

class OpcionCrear(BaseModel):
    letra: str | None = None   # opcional, se ignora al guardar (sin letra fija en DB)
    texto: str
    es_correcta: bool = False


class OpcionDetalle(BaseModel):
    id: int
    letra: str          # generada dinámicamente (A/B/C/D por posición)
    texto: str
    es_correcta: bool


# ─── Pregunta: crear ──────────────────────────────────────────────────────────

class PreguntaCrear(BaseModel):
    materia_id: int
    enunciado: str
    tipo: TipoPregunta = TipoPregunta.opcion_multiple
    nivel_dificultad: NivelDificultad = NivelDificultad.medio
    competencia: str | None = None
    explicacion_texto: str | None = None
    opciones: list[OpcionCrear]
    pista: str | None = None


# ─── Pregunta: editar ─────────────────────────────────────────────────────────

class PreguntaEditar(BaseModel):
    enunciado: str | None = None
    tipo: TipoPregunta | None = None
    nivel_dificultad: NivelDificultad | None = None
    competencia: str | None = None
    explicacion_texto: str | None = None
    esta_activa: bool | None = None
    opciones: list[OpcionCrear] | None = None
    pista: str | None = None


# ─── Pregunta: detalle completo ───────────────────────────────────────────────

class PreguntaDetalle(BaseModel):
    id: int
    materia_id: int
    materia_nombre: str
    enunciado: str
    tipo: TipoPregunta
    nivel_dificultad: NivelDificultad
    competencia: str | None
    explicacion_texto: str | None
    esta_activa: bool
    veces_respondida: int
    veces_incorrecta: int
    opciones: list[OpcionDetalle]
    pista: str | None

    model_config = {"from_attributes": True}


# ─── Listado paginado ─────────────────────────────────────────────────────────

class PreguntaResumen(BaseModel):
    id: int
    materia_nombre: str
    enunciado: str
    nivel_dificultad: NivelDificultad
    tipo: TipoPregunta
    esta_activa: bool
    veces_respondida: int


class PaginacionRespuesta(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    preguntas: list[PreguntaResumen]


# ─── Carga masiva ─────────────────────────────────────────────────────────────

class ResultadoCargaMasiva(BaseModel):
    total_procesadas: int
    total_exitosas: int
    total_fallidas: int
    errores: list[str]
