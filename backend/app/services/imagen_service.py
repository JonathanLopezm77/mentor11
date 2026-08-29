"""
app/services/imagen_service.py
Servicio para subir imágenes a Cloudinary.
"""

import asyncio

import cloudinary
import cloudinary.uploader
from app.core.config import settings


def configurar_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )


def _subir_imagen_sync(contenido: bytes, nombre: str) -> str:
    configurar_cloudinary()
    resultado = cloudinary.uploader.upload(
        contenido,
        folder="mentor11/preguntas",
        public_id=nombre,
        overwrite=True,
        resource_type="image",
        timeout=15,
    )
    return resultado["secure_url"]


async def subir_imagen(contenido: bytes, nombre: str) -> str:
    """
    Sube una imagen a Cloudinary y retorna la URL pública.
    cloudinary.uploader.upload es síncrono y bloqueante (llamada de red) —
    se corre en un hilo aparte para no congelar el event loop mientras sube.
    """
    return await asyncio.to_thread(_subir_imagen_sync, contenido, nombre)
