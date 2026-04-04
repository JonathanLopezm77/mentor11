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

_queue: list[dict] = []
_queue_lock = asyncio.Lock()
_rooms: dict[str, dict] = {}


async def _send(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except Exception:
        pass


async def _close_room_delayed(room_id: str, user_id: int):
    """Espera 15s antes de cerrar la sala — permite reconexión al navegar de página."""
    await asyncio.sleep(15)
    room = _rooms.get(room_id)
    if not room:
        return
    # Verificar si el jugador ya se reconectó
    for p in room["players"]:
        if p["user_id"] == user_id and p.get("reconectado"):
            return
    # No reconectó — notificar al rival y cerrar
    _rooms.pop(room_id, None)
    for p in room["players"]:
        if p["user_id"] != user_id:
            await _send(p["ws"], {
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

    player = {"ws": websocket, "user_id": user_id, "username": username, "reconectado": False}
    room_id: Optional[str] = None

    try:
        # ── Revisar si viene de reconexión (join_room al inicio) ──
        primer_msg = None
        try:
            primer_msg = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)
        except asyncio.TimeoutError:
            primer_msg = None

        if primer_msg and primer_msg.get("type") == "join_room":
            room_id = primer_msg.get("room_id")
            room = _rooms.get(room_id)
            if room:
                for p in room["players"]:
                    if p["user_id"] == user_id:
                        p["ws"] = websocket
                        p["reconectado"] = True
                await _send(websocket, {"type": "rejoined", "room_id": room_id,
                                        "rival": next((p["username"] for p in room["players"] if p["user_id"] != user_id), "")})
            else:
                await _send(websocket, {"type": "room_not_found"})
                return
        else:
            # ── Matchmaking normal ────────────────────────────────
            async with _queue_lock:
                if _queue:
                    rival = _queue.pop(0)
                    room_id = str(uuid.uuid4())
                    _rooms[room_id] = {
                        "players": [rival, player],
                        "mode": None,
                        "host_id": rival["user_id"],
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

            # Procesar el primer mensaje si no fue join_room
            if primer_msg:
                msg_type = primer_msg.get("type")
                if msg_type == "cancel_search":
                    async with _queue_lock:
                        if player in _queue:
                            _queue.remove(player)
                    await _send(websocket, {"type": "search_cancelled"})
                    return

        # ── Bucle principal de mensajes ───────────────────────
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "cancel_search":
                async with _queue_lock:
                    if player in _queue:
                        _queue.remove(player)
                await _send(websocket, {"type": "search_cancelled"})
                break

            if msg_type == "select_mode" and room_id:
                room = _rooms.get(room_id)
                if room and room["host_id"] == user_id and not room.get("mode"):
                    mode = data.get("mode", "aleatorio")
                    room["mode"] = mode
                    for p in room["players"]:
                        await _send(p["ws"], {
                            "type": "mode_selected",
                            "mode": mode,
                            "room_id": room_id,
                        })

            if msg_type == "progress" and room_id:
                room = _rooms.get(room_id)
                if room:
                    for p in room["players"]:
                        if p["user_id"] != user_id:
                            await _send(p["ws"], {
                                "type": "rival_progress",
                                "value": data.get("value", 0),
                            })

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
            # Grace period: esperar 15s antes de cerrar por si el jugador navega de página
            asyncio.create_task(_close_room_delayed(room_id, user_id))
