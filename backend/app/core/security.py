"""
app/core/security.py
Funciones de seguridad: hash de contraseñas y tokens JWT.
Usa bcrypt directamente para evitar incompatibilidades con passlib.

JWT con PyJWT (no python-jose): python-jose está sin mantenimiento y tiene
CVEs conocidos sin parche (confusión de algoritmo, DoS por descompresión) --
PyJWT es el reemplazo estándar, con la misma firma de funciones.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import PyJWTError

from app.core.config import settings


# ─── Contraseñas ──────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Convierte una contraseña en texto plano a un hash bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ─── JWT ──────────────────────────────────────────────────────────────────────


def create_access_token(
    subject: Any,
    expires_delta: timedelta | None = None,
    sid: str | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "access"}
    if sid:
        payload["sid"] = sid
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any, sid: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "refresh"}
    if sid:
        payload["sid"] = sid
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except PyJWTError:
        return None
