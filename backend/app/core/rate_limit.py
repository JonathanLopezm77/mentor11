"""
app/core/rate_limit.py
Rate limiting simple en memoria, por IP, para endpoints públicos sensibles
(login, registro, recuperación de contraseña).

Pensado para un solo worker Uvicorn (no hay estado compartido entre procesos
ni instancias) — si en el futuro se corre con varios workers o réplicas, esto
debe migrar a un backend compartido (ej. Redis).
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_intentos: dict[str, list[float]] = defaultdict(list)


def _ip_cliente(request: Request) -> str:
    # Railway (y cualquier proxy delante de uvicorn) entrega la IP real del
    # usuario en X-Forwarded-For — sin esto, request.client.host sería
    # siempre la IP interna del proxy y todos los usuarios compartirían el
    # mismo límite.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def rate_limiter(max_intentos: int, ventana_seg: int):
    """Devuelve una dependencia de FastAPI que limita a `max_intentos`
    peticiones por IP cada `ventana_seg` segundos, por ruta."""

    async def _dependencia(request: Request):
        ip = _ip_cliente(request)
        ahora = time.monotonic()
        clave = f"{request.url.path}:{ip}"
        intentos = _intentos[clave]

        # Purgar intentos fuera de la ventana
        intentos[:] = [t for t in intentos if ahora - t < ventana_seg]

        if len(intentos) >= max_intentos:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Espera un momento y vuelve a intentarlo.",
            )

        intentos.append(ahora)

    return _dependencia
