"""
app/services/imagen_service.py
Servicio para subir imágenes a Cloudinary.
"""

import cloudinary
import cloudinary.uploader
from app.core.config import settings


def configurar_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )


async def subir_imagen(contenido: bytes, nombre: str) -> str:
    """
    Sube una imagen a Cloudinary y retorna la URL pública.
    """
    configurar_cloudinary()
    resultado = cloudinary.uploader.upload(
        contenido,
        folder="mentor11/preguntas",
        public_id=nombre,
        overwrite=True,
        resource_type="image",
    )
    return resultado["secure_url"]
