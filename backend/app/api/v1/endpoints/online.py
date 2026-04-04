"""
app/api/v1/endpoints/online.py
Modo Online — matchmaking, selección de modo y partida en tiempo real.
Grace period de 15s para reconexión cuando el jugador navega a pregunta_online.html.
"""

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_token

router = APIRouter()

_cola: list[dict] = []
_cola_lock = asyncio.Lock()
_salas: dict[str, dict] = {}


async def _enviar(ws: WebSocket, datos: dict):
    try:
        await ws.send_json(datos)
    except Exception:
        pass


async def _cerrar_sala_delayed(sala_id: str, usuario_id: int):
    """Espera 15s antes de cerrar la sala — permite reconexión al navegar de página."""
    await asyncio.sleep(15)
    sala = _salas.get(sala_id)
    if not sala:
        return
    for p in sala["jugadores"]:
        if p["usuario_id"] == usuario_id and p.get("reconectado"):
            return
    _salas.pop(sala_id, None)
    for p in sala["jugadores"]:
        if p["usuario_id"] != usuario_id:
            await _enviar(p["ws"], {
                "type": "rival_disconnected",
                "msg": "Tu rival se desconectó. Partida cancelada.",
            })


@router.websocket("/ws/online")
async def online_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None

    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    usuario_id: int = int(payload["sub"])
    nombre: str = websocket.query_params.get("username") or f"Jugador{usuario_id}"

    await websocket.accept()

    jugador = {"ws": websocket, "usuario_id": usuario_id, "nombre": nombre, "reconectado": False}
    sala_id: Optional[str] = None

    try:
        # ── Revisar si viene de reconexión (join_room al inicio) ──
        primer_msg = None
        try:
            primer_msg = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)
        except asyncio.TimeoutError:
            primer_msg = None

        if primer_msg and primer_msg.get("type") == "join_room":
            sala_id = primer_msg.get("room_id")
            sala = _salas.get(sala_id)
            if sala:
                for p in sala["jugadores"]:
                    if p["usuario_id"] == usuario_id:
                        p["ws"] = websocket
                        p["reconectado"] = True
                rival = next((p["nombre"] for p in sala["jugadores"] if p["usuario_id"] != usuario_id), "")
                await _enviar(websocket, {"type": "rejoined", "room_id": sala_id, "rival": rival})
            else:
                await _enviar(websocket, {"type": "room_not_found"})
                return
        else:
            # ── Matchmaking normal ────────────────────────────────
            async with _cola_lock:
                if _cola:
                    rival = _cola.pop(0)
                    sala_id = str(uuid.uuid4())
                    _salas[sala_id] = {
                        "jugadores": [rival, jugador],
                        "modo": None,
                        "anfitrion_id": rival["usuario_id"],
                    }
                    await _enviar(rival["ws"], {
                        "type": "match_found",
                        "room_id": sala_id,
                        "rival": nombre,
                        "is_host": True,
                    })
                    await _enviar(websocket, {
                        "type": "match_found",
                        "room_id": sala_id,
                        "rival": rival["nombre"],
                        "is_host": False,
                    })
                else:
                    _cola.append(jugador)
                    await _enviar(websocket, {"type": "searching"})

            if primer_msg:
                if primer_msg.get("type") == "cancel_search":
                    async with _cola_lock:
                        if jugador in _cola:
                            _cola.remove(jugador)
                    await _enviar(websocket, {"type": "search_cancelled"})
                    return

        # ── Bucle principal de mensajes ───────────────────────
        while True:
            datos = await websocket.receive_json()
            tipo = datos.get("type")

            if tipo == "cancel_search":
                async with _cola_lock:
                    if jugador in _cola:
                        _cola.remove(jugador)
                await _enviar(websocket, {"type": "search_cancelled"})
                break

            # El anfitrión entra al bucle con sala_id=None porque la sala se
            # crea en la corrutina del segundo jugador. Buscarla por usuario_id.
            if not sala_id:
                for rid, s in _salas.items():
                    if any(p["usuario_id"] == usuario_id for p in s["jugadores"]):
                        sala_id = rid
                        break

            if tipo == "select_mode" and sala_id:
                sala = _salas.get(sala_id)
                if sala and sala["anfitrion_id"] == usuario_id and not sala.get("modo"):
                    modo = datos.get("mode", "libre")
                    sala["modo"] = modo
                    for p in sala["jugadores"]:
                        await _enviar(p["ws"], {
                            "type": "mode_selected",
                            "mode": modo,
                            "room_id": sala_id,
                        })

            if tipo == "progress" and sala_id:
                sala = _salas.get(sala_id)
                if sala:
                    for p in sala["jugadores"]:
                        if p["usuario_id"] != usuario_id:
                            await _enviar(p["ws"], {
                                "type": "rival_progress",
                                "value": datos.get("value", 0),
                            })

            if tipo == "finish" and sala_id:
                sala = _salas.get(sala_id)
                if sala:
                    mis_correctas = datos.get("correctas", 0)
                    if "finalizados" not in sala:
                        sala["finalizados"] = {}
                    sala["finalizados"][usuario_id] = mis_correctas

                    if len(sala["finalizados"]) == 2:
                        # Ambos terminaron — comparar aciertos
                        ids = list(sala["finalizados"].keys())
                        correctas_a = sala["finalizados"][ids[0]]
                        correctas_b = sala["finalizados"][ids[1]]

                        if correctas_a != correctas_b:
                            ganador_id = ids[0] if correctas_a > correctas_b else ids[1]
                        else:
                            # Empate: gana el primero en terminar
                            ganador_id = sala.get("primer_fin", ids[0])

                        for p in sala["jugadores"]:
                            await _enviar(p["ws"], {
                                "type": "resultado",
                                "ganaste": p["usuario_id"] == ganador_id,
                            })
                        _salas.pop(sala_id, None)
                        sala_id = None
                    else:
                        # Primero en terminar — guardar y esperar al rival
                        sala["primer_fin"] = usuario_id
                break

    except WebSocketDisconnect:
        pass
    finally:
        async with _cola_lock:
            if jugador in _cola:
                _cola.remove(jugador)
        if sala_id:
            asyncio.create_task(_cerrar_sala_delayed(sala_id, usuario_id))
