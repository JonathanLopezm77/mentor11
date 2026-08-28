"""
app/api/v1/endpoints/online.py
Modo Online — matchmaking, selección de modo y partida en tiempo real.
Grace period de 15s para reconexión cuando el jugador navega a pregunta_online.html.
"""

import asyncio
import base64
import io
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from PIL import Image
from sqlalchemy import select

from app.core.security import decode_token
from app.db.database import AsyncSessionLocal
from app.models.usuario import Avatar
from app.services import online_state

router = APIRouter()

AVATAR_THUMB_SIZE = 120


def _redimensionar_avatar_sync(data_uri: str) -> str:
    """Reduce un avatar (tipicamente un PNG de 500x500 compuesto en canvas,
    varias decenas de KB en base64) a una miniatura liviana antes de
    mandarlo por WebSocket. El texto completo del avatar original viajando
    en cada mensaje de match_found es lento/fragil en conexiones moviles.
    Es sincrona/bloqueante (Pillow) — se corre en un hilo aparte."""
    try:
        _, b64data = data_uri.split(",", 1)
        raw = base64.b64decode(b64data)
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        img.thumbnail((AVATAR_THUMB_SIZE, AVATAR_THUMB_SIZE), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        nuevo_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{nuevo_b64}"
    except Exception:
        return data_uri  # si algo falla, se manda el original como respaldo


async def _obtener_avatar(usuario_id: int) -> str | None:
    async with AsyncSessionLocal() as db:
        resultado = await db.execute(
            select(Avatar.imagen_src).where(Avatar.usuario_id == usuario_id)
        )
        imagen_src = resultado.scalar_one_or_none()

    if not imagen_src or not imagen_src.startswith("data:image"):
        return imagen_src

    return await asyncio.to_thread(_redimensionar_avatar_sync, imagen_src)

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
    online_state.limpiar_sala(sala_id)
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
                    "poderes": online_state.inventario_de(usuario_id),
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
                    online_state.crear_sala(sala_id, [rival["usuario_id"], usuario_id])
                    await _enviar(rival["ws"], {
                        "type": "match_found",
                        "room_id": sala_id,
                        "rival": nombre,
                        "rival_avatar": jugador["avatar"],
                        "is_host": True,
                        "poderes": online_state.inventario_de(rival["usuario_id"]),
                    })
                    await _enviar(websocket, {
                        "type": "match_found",
                        "room_id": sala_id,
                        "rival": rival["nombre"],
                        "rival_avatar": rival["avatar"],
                        "is_host": False,
                        "poderes": online_state.inventario_de(usuario_id),
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

            if tipo == "listo" and sala_id:
                sala = _salas.get(sala_id)
                if sala:
                    sala.setdefault("listos", set()).add(usuario_id)
                    if len(sala["listos"]) >= 2:
                        for p in sala["jugadores"]:
                            await _enviar(p["ws"], {"type": "iniciar_partida"})
                    else:
                        for p in sala["jugadores"]:
                            if p["usuario_id"] != usuario_id:
                                await _enviar(p["ws"], {"type": "rival_listo"})

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
                    valor = datos.get("value", 0)
                    sala.setdefault("progreso", {})[usuario_id] = valor
                    for p in sala["jugadores"]:
                        if p["usuario_id"] != usuario_id:
                            await _enviar(p["ws"], {
                                "type": "rival_progress",
                                "value": valor,
                            })

            if tipo == "usar_poder" and sala_id:
                sala = _salas.get(sala_id)
                poder_id = datos.get("poder")
                rival_id = online_state.rival_de(usuario_id)
                rival_p = next((p for p in sala["jugadores"] if p["usuario_id"] == rival_id), None) if sala else None

                if not sala or poder_id not in online_state.PODERES or rival_id is None:
                    await _enviar(websocket, {"type": "poder_error", "poder": poder_id, "mensaje": "Poder invalido"})
                elif not online_state.consumir_poder(usuario_id, poder_id):
                    await _enviar(websocket, {"type": "poder_error", "poder": poder_id, "mensaje": "No posees ese poder"})
                else:
                    if poder_id == "doble_puntos":
                        online_state.activar_efecto(usuario_id, "doble_puntos", online_state.DURACION_X2_S)
                        await _enviar(websocket, {"type": "efecto_propio", "poder": poder_id, "duracion_s": online_state.DURACION_X2_S})

                    elif poder_id == "equivocarse":
                        online_state.otorgar_proteccion(usuario_id)
                        await _enviar(websocket, {"type": "efecto_propio", "poder": poder_id})

                    elif poder_id == "cambiar_orden":
                        online_state.activar_efecto(rival_id, "cambiar_orden", online_state.DURACION_CAMBIAR_ORDEN_S)
                        if rival_p:
                            await _enviar(rival_p["ws"], {"type": "orden_alterado", "duracion_s": online_state.DURACION_CAMBIAR_ORDEN_S})

                    elif poder_id == "congelar":
                        online_state.activar_efecto(rival_id, "congelar", online_state.DURACION_CONGELAR_S)
                        if rival_p:
                            await _enviar(rival_p["ws"], {"type": "congelado", "duracion_s": online_state.DURACION_CONGELAR_S})

                    elif poder_id == "devolver_rival_2":
                        if rival_p:
                            await _enviar(rival_p["ws"], {"type": "repetir_preguntas", "cantidad": 2})

                    elif poder_id == "robar_poder":
                        robado = online_state.robar_poder_aleatorio(usuario_id)
                        await _enviar(websocket, {"type": "inventario_actualizado", "poderes": online_state.inventario_de(usuario_id), "robado": robado})
                        if rival_p:
                            await _enviar(rival_p["ws"], {"type": "inventario_actualizado", "poderes": online_state.inventario_de(rival_id), "robado": None})

                    if poder_id != "robar_poder":
                        await _enviar(websocket, {"type": "poder_usado", "poder": poder_id})

            if tipo == "finish" and sala_id:
                sala = _salas.get(sala_id)
                if not sala or sala.get("terminada"):
                    break  # la sala ya no existe o el rival ya termino primero

                sala["terminada"] = True

                mis_correctas = datos.get("correctas", 0)
                otro = next((p for p in sala["jugadores"] if p["usuario_id"] != usuario_id), None)
                rival_id = otro["usuario_id"] if otro else None

                mis_puntos = online_state.puntos_de(usuario_id)
                rival_puntos = online_state.puntos_de(rival_id) if rival_id is not None else 0
                # El rival puede seguir jugando — no sabemos cuantas tiene correctas,
                # solo su ultimo % de progreso reportado.
                rival_progreso_pct = sala.get("progreso", {}).get(rival_id, 0) if rival_id is not None else 0

                if mis_puntos == rival_puntos:
                    resultado_mio = {"type": "resultado", "empate": True, "ganaste": False, "mis_correctas": mis_correctas, "rival_correctas": None, "rival_progreso_pct": rival_progreso_pct, "mis_puntos": mis_puntos, "rival_puntos": rival_puntos}
                    resultado_rival = {"type": "resultado", "empate": True, "ganaste": False, "mis_correctas": None, "rival_correctas": mis_correctas, "mis_puntos": rival_puntos, "rival_puntos": mis_puntos}
                else:
                    yo_gane = mis_puntos > rival_puntos
                    resultado_mio = {"type": "resultado", "empate": False, "ganaste": yo_gane, "mis_correctas": mis_correctas, "rival_correctas": None, "rival_progreso_pct": rival_progreso_pct, "mis_puntos": mis_puntos, "rival_puntos": rival_puntos}
                    resultado_rival = {"type": "resultado", "empate": False, "ganaste": not yo_gane, "mis_correctas": None, "rival_correctas": mis_correctas, "mis_puntos": rival_puntos, "rival_puntos": mis_puntos}

                await _enviar(websocket, resultado_mio)
                if otro:
                    await _enviar(otro["ws"], resultado_rival)

                _salas.pop(sala_id, None)
                online_state.limpiar_sala(sala_id)
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
