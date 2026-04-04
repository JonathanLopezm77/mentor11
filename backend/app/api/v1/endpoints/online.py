"""
app/api/v1/endpoints/online.py
Modo Online — matchmaking, selección de modo y partida en tiempo real.
"""

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_token

router = APIRouter()

_queue: list[dict] = []
_queue_lock = asyncio.Lock()
_rooms: dict[str, dict] = {}


async def _send(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except Exception:
        pass


async def _close_room(room_id: str, disconnected_user_id: int):
    room = _rooms.pop(room_id, None)
    if not room:
        return
    for player in room["players"]:
        if player["user_id"] != disconnected_user_id:
            await _send(player["ws"], {
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

    user_id: int = int(payload["sub"])
    username: str = websocket.query_params.get("username") or f"Jugador{user_id}"

    await websocket.accept()

    player = {"ws": websocket, "user_id": user_id, "username": username}
    room_id: Optional[str] = None

    try:
        async with _queue_lock:
            if _queue:
                rival = _queue.pop(0)
                room_id = str(uuid.uuid4())
                _rooms[room_id] = {
                    "players": [rival, player],
                    "mode": None,
                    "host_id": rival["user_id"],  # quien esperaba = host, elige modo
                }
                await _send(rival["ws"], {
                    "type": "match_found",
                    "room_id": room_id,
                    "rival": username,
                    "is_host": True,
                })
                await _send(websocket, {
                    "type": "match_found",
                    "room_id": room_id,
                    "rival": rival["username"],
                    "is_host": False,
                })
            else:
                _queue.append(player)
                await _send(websocket, {"type": "searching"})

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "cancel_search":
                async with _queue_lock:
                    if player in _queue:
                        _queue.remove(player)
                await _send(websocket, {"type": "search_cancelled"})
                break

            # Host elige el modo de juego
            if msg_type == "select_mode" and room_id:
                room = _rooms.get(room_id)
                if room and room["host_id"] == user_id and not room.get("mode"):
                    mode = data.get("mode", "aleatorio")
                    room["mode"] = mode
                    for p in room["players"]:
                        await _send(p["ws"], {
                            "type": "mode_selected",
                            "mode": mode,
                        })

            # Actualización de progreso (reenviar al rival)
            if msg_type == "progress" and room_id:
                room = _rooms.get(room_id)
                if room:
                    for p in room["players"]:
                        if p["user_id"] != user_id:
                            await _send(p["ws"], {
                                "type": "rival_progress",
                                "value": data.get("value", 0),
                            })

            # Jugador terminó primero
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
        async with _queue_lock:
            if player in _queue:
                _queue.remove(player)
        if room_id:
            await _close_room(room_id, user_id)
