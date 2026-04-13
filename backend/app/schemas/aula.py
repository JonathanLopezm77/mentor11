"""
app/schemas/aula.py
Esquemas Pydantic para aulas, tareas y progreso.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Aula ──────────────────────────────────────────────────────────────────────

class CrearAulaRequest(BaseModel):
    nombre: str
    materia_id: int
    color_hex: Optional[str] = None


class AulaRespuesta(BaseModel):
    id: int
    nombre: str
    codigo_acceso: str
    materia_id: Optional[int]
    materia_nombre: Optional[str]
    profesor_nombre: str
    esta_activa: bool
    creada_en: datetime
    total_estudiantes: int

    class Config:
        from_attributes = True


class UnirseAulaRequest(BaseModel):
    codigo: str


# ── Estudiante en aula ─────────────────────────────────────────────────────────

class EstudianteEnAula(BaseModel):
    id: int
    username: str
    avatar: Optional[str]
    tareas_completadas: int
    total_tareas: int


# ── Tarea ─────────────────────────────────────────────────────────────────────

class CrearTareaRequest(BaseModel):
    cantidad_preguntas: int = 10


class TareaRespuesta(BaseModel):
    id: int
    aula_id: int
    cantidad_preguntas: int
    creada_en: datetime
    completada_por: int   # cuántos estudiantes la completaron
    total_estudiantes: int

    class Config:
        from_attributes = True


class TareaEstudianteRespuesta(BaseModel):
    id: int
    aula_id: int
    aula_nombre: str
    materia_id: Optional[int]
    materia_nombre: Optional[str]
    cantidad_preguntas: int
    creada_en: datetime
    completada: bool
    sesion_id: Optional[int]

    class Config:
        from_attributes = True


# ── Ranking ───────────────────────────────────────────────────────────────────

class EntradaRanking(BaseModel):
    posicion: int
    usuario_id: int
    username: str
    avatar: Optional[str]
    porcentaje_acierto: float
    total_respondidas: int


class RankingAulaRespuesta(BaseModel):
    top: list[EntradaRanking]
    bottom: list[EntradaRanking]
    materia_nombre: str


# ── Stats grupo ───────────────────────────────────────────────────────────────

class StatsGrupo(BaseModel):
    total_estudiantes: int
    promedio_acierto: float
    total_respondidas: int
    total_tareas: int
    tareas_completadas_total: int
    materia_nombre: str


# ── Stats individuales ────────────────────────────────────────────────────────

class StatsIndividual(BaseModel):
    usuario_id: int
    username: str
    avatar: Optional[str]
    porcentaje_acierto: float
    total_respondidas: int
    total_correctas: int
    tareas_completadas: int
    total_tareas: int


# ── Detalle de aula ───────────────────────────────────────────────────────────

class AulaDetalleRespuesta(BaseModel):
    id: int
    nombre: str
    codigo_acceso: str
    materia_id: Optional[int]
    materia_nombre: Optional[str]
    creada_en: datetime
    total_estudiantes: int
    estudiantes: list[EstudianteEnAula]
    tareas: list[TareaRespuesta]

    class Config:
        from_attributes = True
