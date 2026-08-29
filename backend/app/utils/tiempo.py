"""
app/utils/tiempo.py
Utilidades de zona horaria.

Todo se guarda en la base de datos en UTC naive (convención: datetime.utcnow()).
Estas funciones convierten a hora de Bogotá (America/Bogota, UTC-5 fijo, sin
horario de verano) solo para decidir "qué día es" desde la perspectiva del
estudiante — racha diaria y límites de mes en /perfil/estadisticas. Los
timestamps en la base de datos NO cambian de formato, solo la comparación.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

_UTC = ZoneInfo("UTC")
_BOGOTA = ZoneInfo("America/Bogota")


def utc_a_bogota(dt: datetime) -> datetime:
    """Convierte un datetime naive (asumido UTC) a datetime aware en hora de Bogotá."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_UTC)
    return dt.astimezone(_BOGOTA)


def hoy_en_bogota() -> "datetime.date":
    """Fecha (día calendario) actual en Bogotá, a partir del reloj UTC del servidor."""
    return utc_a_bogota(datetime.utcnow()).date()


def bogota_a_utc(dt_bogota: datetime) -> datetime:
    """Convierte un datetime aware en hora de Bogotá (o naive, asumido Bogotá)
    a datetime naive UTC — para usar como límite en consultas contra columnas
    guardadas en UTC."""
    if dt_bogota.tzinfo is None:
        dt_bogota = dt_bogota.replace(tzinfo=_BOGOTA)
    return dt_bogota.astimezone(_UTC).replace(tzinfo=None)
