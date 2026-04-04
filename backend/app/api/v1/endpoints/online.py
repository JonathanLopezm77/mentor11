"""
app/api/v1/endpoints/online.py
Modo Online — WebSocket matchmaking y sala de partida en tiempo real.

Flujo:
  1. El cliente se conecta a /ws/online?token=<JWT>
  2. El servidor valida el token y extrae usuario_id + username
  3. Si hay alguien esperando en la cola → se forma una sala (Room)
     Si no → el jugador espera en la cola
  4. Ambos jugadores reciben { "type": "match_found", "rival": "..." }
  5. Durante la partida el cliente manda { "type": "progress", "value": 0-100 }
     y el servidor se lo reenvía al rival
  6. Cuando alguien manda { "type": "finish" } se notifica al rival que perdió
  7. Al desconectarse se limpia la sala y se notifica al rival
"""

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token

router = APIRouter()


# ── Cola de matchmaking ───────────────────────────────────────────────────────
# Cada entrada: {"ws": WebSocket, "user_id": int, "username": str}
_queue: list[dict] = []
_queue_lock = asyncio.Lock()

# ── Salas activas ─────────────────────────────────────────────────────────────
# room_id → {"players": [{"ws": WebSocket, "user_id": int, "username": str}, ...]}
_rooms: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _send(ws: WebSocket, data: dict):
    """Envía JSON al cliente de forma segura."""
    try:
        await ws.send_json(data)
    except Exception:
        pass


async def _close_room(room_id: str, disconnected_user_id: int):
    """Notifica al rival y elimina la sala."""
    room = _rooms.pop(room_id, None)
    if not room:
        return
    for player in room["players"]:
        if player["user_id"] != disconnected_user_id:
            await _send(player["ws"], {
                "type": "rival_disconnected",
                "msg": "Tu rival se desconectó. Partida cancelada.",
            })


# ── Endpoint WebSocket ────────────────────────────────────────────────────────

@router.websocket("/ws/online")
async def online_ws(websocket: WebSocket):
    """
    Punto de entrada único para el modo online.
    Autenticación: token JWT como query param  ?token=<access_token>
    """
    # 1. Validar token antes de aceptar la conexión
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None

    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)   # 4001 = No autorizado
        return

    user_id: int = int(payload["sub"])
    username: str = websocket.query_params.get("username") or f"Jugador{user_id}"

    await websocket.accept()

    player = {"ws": websocket, "user_id": user_id, "username": username}
    room_id: Optional[str] = None

    try:
        # 2. Matchmaking
        async with _queue_lock:
            if _queue:
                # Hay alguien esperando → formar sala
                rival = _queue.pop(0)
                room_id = str(uuid.uuid4())
                _rooms[room_id] = {"players": [rival, player]}

                # Notificar a ambos
                await _send(rival["ws"], {
                    "type": "match_found",
                    "room_id": room_id,
                    "rival": username,
                })
                await _send(websocket, {
                    "type": "match_found",
                    "room_id": room_id,
                    "rival": rival["username"],
                })
            else:
                # Cola vacía → esperar
                _queue.append(player)
                await _send(websocket, {"type": "searching"})

        # 3. Bucle de mensajes
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # Si todavía estaba buscando partida y se cancela
            if msg_type == "cancel_search":
                async with _queue_lock:
                    if player in _queue:
                        _queue.remove(player)
                await _send(websocket, {"type": "search_cancelled"})
                break

            # Reenviar progreso al rival
            if msg_type == "progress" and room_id:
                room = _rooms.get(room_id)
                if room:
                    for p in room["players"]:
                        if p["user_id"] != user_id:
                            await _send(p["ws"], {
                                "type": "rival_progress",
                                "value": data.get("value", 0),
                            })

            # El jugador terminó primero
            if msg_type == "finish" and room_id:
                room = _rooms.get(room_id)
                if room:
                    for p in room["players"]:
                        if p["user_id"] != user_id:
                            await _send(p["ws"], {"type": "rival_finished"})
                    await _send(websocket, {"type": "you_win"})
                    _rooms.pop(room_id, None)
                    room_id = None
                break

    except WebSocketDisconnect:
        pass
    finally:
        # Limpiar cola si seguía esperando
        async with _queue_lock:
            if player in _queue:
                _queue.remove(player)
        # Limpiar sala si estaba en partida
        if room_id:
            await _close_room(room_id, user_id)
