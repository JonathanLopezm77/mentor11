"""
app/models/__init__.py

Importa todos los modelos en un solo lugar.
Esto es CRÍTICO para Alembic: al hacer `from app.models import *`
en env.py, Alembic detecta todas las tablas y genera las migraciones correctamente.
"""
from app.models.usuario import Usuario, Avatar, Suscripcion, TokenRecuperacion, RolUsuario, PlanSuscripcion
from app.models.contenido import Materia, Texto, Pregunta, Respuesta, Pista, TipoPregunta, NivelDificultad
from app.models.juego import SesionJuego, RespuestaUsuario, EstadisticaUsuario, PartidaOnline, PoderPartida, ModoJuego, ModoPartida, EstadoPartida
from app.models.aula import Aula, AulaEstudiante, RankingAula, Reto, PeriodoRanking, EstadoReto
from app.models.sistema import Reporte, Notificacion, LogActividad, Logro, UsuarioLogro

__all__ = [
    # Usuario
    "Usuario", "Avatar", "Suscripcion", "TokenRecuperacion", "RolUsuario", "PlanSuscripcion",
    # Contenido
    "Materia", "Texto", "Pregunta", "Respuesta", "Pista", "TipoPregunta", "NivelDificultad",
    # Juego
    "SesionJuego", "RespuestaUsuario", "EstadisticaUsuario", "PartidaOnline", "PoderPartida",
    "ModoJuego", "ModoPartida", "EstadoPartida",
    # Aula
    "Aula", "AulaEstudiante", "RankingAula", "Reto", "PeriodoRanking", "EstadoReto",
    # Sistema
    "Reporte", "Notificacion", "LogActividad", "Logro", "UsuarioLogro",
]
