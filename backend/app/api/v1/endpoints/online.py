"""
app/api/v1/endpoints/online.py
Modo Online — matchmaking, selección de modo y partida en tiempo real.
Grace period de 15s para reconexión cuando el jugador navega a pregunta_online.html.
"""

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.security import decode_token
from app.db.database import AsyncSessionLocal
from app.models.usuario import Avatar

router = APIRouter()


async def _obtener_avatar(usuario_id: int) -> str | None:
    async with AsyncSessionLocal() as db:
        resultado = await db.execute(
            select(Avatar.imagen_src).where(Avatar.usuario_id == usuario_id)
        )
        return resultado.scalar_one_or_none()

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

    avatar = await _obtener_avatar(usuario_id)
    jugador = {"ws": websocket, "usuario_id": usuario_id, "nombre": nombre, "avatar": avatar, "reconectado": False}
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
                rival_p = next((p for p in sala["jugadores"] if p["usuario_id"] != usuario_id), None)
                await _enviar(websocket, {
                    "type": "rejoined",
                    "room_id": sala_id,
                    "rival": rival_p["nombre"] if rival_p else "",
                    "rival_avatar": rival_p["avatar"] if rival_p else None,
                })
            else:
                await _enviar(websocket, {"type": "room_not_found"})
                return
        else:
            # ── Matchmaking normal ────────────────────────────────
            async with _cola_lock:
                # Buscar rival que no sea el mismo usuario
                rival_encontrado = None
                for candidato in _cola:
                    if candidato["usuario_id"] != usuario_id:
                        rival_encontrado = candidato
                        _cola.remove(candidato)
                        break

                if rival_encontrado:
                    rival = rival_encontrado
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
                        "rival_avatar": jugador["avatar"],
                        "is_host": True,
                    })
                    await _enviar(websocket, {
                        "type": "match_found",
                        "room_id": sala_id,
                        "rival": rival["nombre"],
                        "rival_avatar": rival["avatar"],
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
                    materia_ids = datos.get("materia_ids", None)
                    cantidad = datos.get("cantidad", 10)
                    for p in sala["jugadores"]:
                        await _enviar(p["ws"], {
                            "type": "mode_selected",
                            "mode": modo,
                            "room_id": sala_id,
                            "materia_ids": materia_ids,
                            "cantidad": cantidad,
                        })

            if tipo == "configurando_libre" and sala_id:
                # El anfitrión abrió la pantalla de config — avisar al rival
                sala = _salas.get(sala_id)
                if sala:
                    for p in sala["jugadores"]:
                        if p["usuario_id"] != usuario_id:
                            await _enviar(p["ws"], {"type": "modo_configurando"})

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
                if not sala:
                    break

                mis_correctas = datos.get("correctas", 0)
                if "finalizados" not in sala:
                    sala["finalizados"] = {}
                if "evento_fin" not in sala:
                    sala["evento_fin"] = asyncio.Event()

                sala["finalizados"][usuario_id] = mis_correctas

                if len(sala["finalizados"]) == 2:
                    # Calcular resultados individuales
                    ids = list(sala["finalizados"].keys())
                    c0 = sala["finalizados"][ids[0]]
                    c1 = sala["finalizados"][ids[1]]
                    if c0 == c1:
                        sala["resultados_fin"] = {
                            ids[0]: {"type": "resultado", "empate": True, "ganaste": False, "mis_correctas": c0, "rival_correctas": c1},
                            ids[1]: {"type": "resultado", "empate": True, "ganaste": False, "mis_correctas": c1, "rival_correctas": c0},
                        }
                    else:
                        ganador = ids[0] if c0 > c1 else ids[1]
                        sala["resultados_fin"] = {
                            ids[0]: {"type": "resultado", "empate": False, "ganaste": ids[0] == ganador, "mis_correctas": c0, "rival_correctas": c1},
                            ids[1]: {"type": "resultado", "empate": False, "ganaste": ids[1] == ganador, "mis_correctas": c1, "rival_correctas": c0},
                        }
                    sala["evento_fin"].set()  # Notificar a ambas corrutinas

                # Ambos jugadores esperan el evento con keep-alive cada 20s
                evento = sala["evento_fin"]
                tarea_evento = asyncio.ensure_future(evento.wait())
                while not tarea_evento.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(tarea_evento), timeout=20.0)
                    except asyncio.TimeoutError:
                        if evento.is_set():
                            break
                        # Mantener conexión viva mientras esperamos al rival
                        await _enviar(websocket, {"type": "esperando_rival"})
                        if not _salas.get(sala_id):
                            tarea_evento.cancel()
                            break

                # Cada jugador envía el resultado desde su propia corrutina
                sala_final = _salas.get(sala_id)
                if sala_final and "resultados_fin" in sala_final:
                    mi_resultado = sala_final["resultados_fin"].get(usuario_id)
                    if mi_resultado:
                        await _enviar(websocket, mi_resultado)
                    # Limpiar sala cuando ambos han recibido
                    sala_final.setdefault("fin_confirmados", set()).add(usuario_id)
                    if len(sala_final["fin_confirmados"]) >= 2:
                        _salas.pop(sala_id, None)
                        sala_id = None

                break  # salir del bucle principal

    except WebSocketDisconnect:
        pass
    finally:
        async with _cola_lock:
            if jugador in _cola:
                _cola.remove(jugador)
        if sala_id:
            asyncio.create_task(_cerrar_sala_delayed(sala_id, usuario_id))
