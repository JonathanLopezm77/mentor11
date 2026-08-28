"""
app/services/online_state.py
Estado en memoria de los poderes del modo Online — inventario por jugador,
efectos temporales activos y puntaje de la partida (usado para decidir el
ganador cuando doble_puntos esta activo). Vive en memoria, igual que las
salas de matchmaking en online.py; se descarta cuando termina la partida.
"""

import random
import time

PODERES = [
    "cambiar_orden",
    "mitad_mitad",
    "doble_puntos",
    "robar_poder",
    "setenta_cinco",
    "devolver_rival_2",
    "equivocarse",
    "congelar",
]

DURACION_X2_S = 30
DURACION_CAMBIAR_ORDEN_S = 30
DURACION_CONGELAR_S = 20

# sala_id -> {
#   "jugadores": [usuario_id, usuario_id],
#   "poderes": {usuario_id: {poder_id: cantidad}},
#   "efectos": {usuario_id: {poder_id: expira_en_epoch}},
#   "protegido": {usuario_id: bool},
#   "puntos": {usuario_id: int},
# }
_salas: dict[str, dict] = {}
_usuario_a_sala: dict[int, str] = {}


def crear_sala(sala_id: str, usuario_ids: list[int]) -> None:
    poderes: dict[int, dict[str, int]] = {}
    for uid in usuario_ids:
        elegidos = random.sample(PODERES, 3)
        poderes[uid] = {p: 1 for p in elegidos}

    _salas[sala_id] = {
        "jugadores": list(usuario_ids),
        "poderes": poderes,
        "efectos": {uid: {} for uid in usuario_ids},
        "protegido": {uid: False for uid in usuario_ids},
        "puntos": {uid: 0 for uid in usuario_ids},
    }
    for uid in usuario_ids:
        _usuario_a_sala[uid] = sala_id


def limpiar_sala(sala_id: str) -> None:
    sala = _salas.pop(sala_id, None)
    if not sala:
        return
    for uid in sala["jugadores"]:
        if _usuario_a_sala.get(uid) == sala_id:
            _usuario_a_sala.pop(uid, None)


def _sala_de(usuario_id: int) -> dict | None:
    sala_id = _usuario_a_sala.get(usuario_id)
    if not sala_id:
        return None
    return _salas.get(sala_id)


def usuario_en_sala(usuario_id: int) -> bool:
    return _sala_de(usuario_id) is not None


def rival_de(usuario_id: int) -> int | None:
    sala = _sala_de(usuario_id)
    if not sala:
        return None
    for uid in sala["jugadores"]:
        if uid != usuario_id:
            return uid
    return None


def inventario_de(usuario_id: int) -> dict[str, int]:
    sala = _sala_de(usuario_id)
    if not sala:
        return {}
    return dict(sala["poderes"].get(usuario_id, {}))


def posee_poder(usuario_id: int, poder_id: str) -> bool:
    sala = _sala_de(usuario_id)
    if not sala:
        return False
    return sala["poderes"].get(usuario_id, {}).get(poder_id, 0) > 0


def consumir_poder(usuario_id: int, poder_id: str) -> bool:
    """Descuenta 1 unidad del poder si el jugador lo posee. True si se consumio."""
    sala = _sala_de(usuario_id)
    if not sala:
        return False
    cantidad = sala["poderes"].get(usuario_id, {}).get(poder_id, 0)
    if cantidad <= 0:
        return False
    sala["poderes"][usuario_id][poder_id] = cantidad - 1
    return True


def robar_poder_aleatorio(usuario_id: int) -> str | None:
    """El usuario le roba un poder al azar a su rival. Devuelve el poder_id robado o None."""
    rival_id = rival_de(usuario_id)
    if rival_id is None:
        return None
    sala = _sala_de(usuario_id)
    disponibles = [p for p, c in sala["poderes"].get(rival_id, {}).items() if c > 0]
    if not disponibles:
        return None
    elegido = random.choice(disponibles)
    sala["poderes"][rival_id][elegido] -= 1
    sala["poderes"].setdefault(usuario_id, {})
    sala["poderes"][usuario_id][elegido] = sala["poderes"][usuario_id].get(elegido, 0) + 1
    return elegido


def activar_efecto(usuario_id: int, poder_id: str, duracion_s: int) -> None:
    sala = _sala_de(usuario_id)
    if not sala:
        return
    sala["efectos"].setdefault(usuario_id, {})[poder_id] = time.time() + duracion_s


def efecto_activo(usuario_id: int, poder_id: str) -> bool:
    sala = _sala_de(usuario_id)
    if not sala:
        return False
    expira = sala["efectos"].get(usuario_id, {}).get(poder_id)
    return expira is not None and time.time() < expira


def otorgar_proteccion(usuario_id: int) -> None:
    sala = _sala_de(usuario_id)
    if not sala:
        return
    sala["protegido"][usuario_id] = True


def tiene_proteccion(usuario_id: int) -> bool:
    sala = _sala_de(usuario_id)
    if not sala:
        return False
    return sala["protegido"].get(usuario_id, False)


def consumir_proteccion(usuario_id: int) -> bool:
    sala = _sala_de(usuario_id)
    if not sala or not sala["protegido"].get(usuario_id, False):
        return False
    sala["protegido"][usuario_id] = False
    return True


def sumar_puntos(usuario_id: int, monto: int) -> None:
    sala = _sala_de(usuario_id)
    if not sala:
        return
    sala["puntos"][usuario_id] = sala["puntos"].get(usuario_id, 0) + monto


def puntos_de(usuario_id: int) -> int:
    sala = _sala_de(usuario_id)
    if not sala:
        return 0
    return sala["puntos"].get(usuario_id, 0)


def puntos_por_respuesta(usuario_id: int, es_correcta: bool) -> tuple[int, bool]:
    """Calcula y aplica los puntos de una respuesta, respetando doble_puntos
    y la proteccion de 'equivocarse'. Devuelve (monto_sumado, proteccion_usada)."""
    if not usuario_en_sala(usuario_id):
        return 0, False

    correcta_efectiva = es_correcta
    proteccion_usada = False
    if not es_correcta and consumir_proteccion(usuario_id):
        correcta_efectiva = True
        proteccion_usada = True

    if not correcta_efectiva:
        return 0, False

    monto = 20 if efecto_activo(usuario_id, "doble_puntos") else 10
    sumar_puntos(usuario_id, monto)
    return monto, proteccion_usada
