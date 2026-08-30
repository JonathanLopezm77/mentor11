"""
app/api/v1/endpoints/admin.py
Endpoints del panel de administración.
Solo accesibles con rol admin_tech.
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin, get_db
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
from app.schemas.admin import (
    PreguntaCrear,
    PreguntaEditar,
    PreguntaDetalle,
    PaginacionRespuesta,
    ResultadoCargaMasiva,
)
from app.services.admin_service import (
    crear_pregunta,
    listar_preguntas,
    obtener_pregunta,
    editar_pregunta,
    eliminar_pregunta,
    cargar_preguntas_csv,
    AdminError,
)
from app.services.imagen_service import subir_imagen

router = APIRouter()


# ─── Listar textos existentes ────────────────────────────────────────────────


@router.get("/textos")
async def listar_textos(
    materia_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    from sqlalchemy import select as sa_select
    from app.models.contenido import Texto

    query = sa_select(Texto).where(Texto.esta_activo == True)
    if materia_id:
        query = query.where(Texto.materia_id == materia_id)
    query = query.order_by(Texto.id.desc())
    res = await db.execute(query)
    textos = res.scalars().all()
    return [
        {
            "id": t.id,
            "titulo": t.titulo or f"Texto #{t.id}",
            "preview": t.contenido[:80] + ("..." if len(t.contenido) > 80 else ""),
        }
        for t in textos
    ]


# ─── Listar preguntas ─────────────────────────────────────────────────────────


@router.get("/preguntas", response_model=PaginacionRespuesta)
async def listar(
    materia_id: int | None = Query(None),
    nivel: str | None = Query(None),
    activa: bool | None = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    return await listar_preguntas(db, materia_id, nivel, activa, pagina, por_pagina)


# ─── Descargar plantilla CSV ──────────────────────────────────────────────────


@router.get("/preguntas/plantilla")
async def descargar_plantilla(admin: Usuario = Depends(get_admin)):
    from fastapi.responses import Response

    plantilla = (
        "materia_codigo;enunciado;nivel;opcion_a;imagen_a;opcion_b;imagen_b;opcion_c;imagen_c;opcion_d;imagen_d;correcta;explicacion;pista;imagen_url\n"
        "MAT;¿Cuánto es 2 + 2?;facil;3;;4;;5;;6;;B;La suma de 2 + 2 es 4;Piensa en contar con los dedos;\n"
        "LC;¿Qué figura retórica es 'el tiempo es oro'?;medio;Metáfora;;Hipérbole;;Símil;;Paradoja;;A;"
        "Una metáfora compara sin usar 'como';Piensa en comparaciones directas;\n"
        "ING;Choose the correct verb: She ___ to school;facil;go;;goes;;going;;gone;;B;"
        "Third person singular uses -s;Think about he/she/it;\n"
        "CN;¿Cuál figura corresponde a un triángulo?;medio;;;https://cloudinary.com/triangulo.png;;https://cloudinary.com/cuadrado.png;;https://cloudinary.com/circulo.png;;https://cloudinary.com/rombo.png;A;El triángulo tiene 3 lados;;\n"
    )

    return Response(
        content=plantilla.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_preguntas.csv"},
    )


# ─── Subir imagen ─────────────────────────────────────────────────────────────

MAX_IMAGEN_BYTES = 8 * 1024 * 1024  # 8 MB

_FIRMAS_IMAGEN = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}


def _tipo_imagen_real(contenido: bytes) -> str | None:
    """Detecta el tipo real de imagen por los primeros bytes del archivo
    (magic bytes), no por la extensión del nombre — un .png renombrado que
    en realidad no es una imagen no pasa este chequeo (ver SEC-04)."""
    for firma, tipo in _FIRMAS_IMAGEN.items():
        if contenido.startswith(firma):
            return tipo
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("/imagenes/subir")
async def subir_imagen_pregunta(
    imagen: UploadFile = File(..., description="Imagen PNG, JPG o WebP"),
    admin: Usuario = Depends(get_admin),
):
    """
    Sube una imagen a Cloudinary y retorna la URL pública.
    Usar esta URL en el campo imagen_url al crear una pregunta.
    """
    extensiones_validas = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    if not imagen.filename.lower().endswith(extensiones_validas):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan imágenes PNG, JPG, JPEG, WebP o GIF",
        )

    contenido = await imagen.read()
    if len(contenido) == 0:
        raise HTTPException(status_code=400, detail="La imagen está vacía")
    if len(contenido) > MAX_IMAGEN_BYTES:
        raise HTTPException(status_code=413, detail="La imagen no puede superar 8 MB")
    if _tipo_imagen_real(contenido) is None:
        raise HTTPException(
            status_code=400,
            detail="El archivo no es una imagen válida (PNG, JPG, WebP o GIF)",
        )

    try:
        nombre = f"pregunta_{uuid.uuid4().hex[:8]}"
        url = await subir_imagen(contenido, nombre)
        return {"imagen_url": url}
    except Exception:
        logger.exception("Error al subir imagen (admin_id=%s)", admin.id)
        raise HTTPException(status_code=500, detail="Error al subir la imagen. Intenta de nuevo.")


# ─── Ver detalle de una pregunta ──────────────────────────────────────────────


@router.get("/preguntas/{pregunta_id}", response_model=PreguntaDetalle)
async def ver_pregunta(
    pregunta_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    try:
        return await obtener_pregunta(db, pregunta_id)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Crear pregunta individual ────────────────────────────────────────────────


@router.post("/preguntas", response_model=PreguntaDetalle, status_code=201)
async def crear(
    datos: PreguntaCrear,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    try:
        return await crear_pregunta(db, admin.id, datos)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Editar pregunta ──────────────────────────────────────────────────────────


@router.put("/preguntas/{pregunta_id}", response_model=PreguntaDetalle)
async def editar(
    pregunta_id: int,
    datos: PreguntaEditar,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    try:
        return await editar_pregunta(db, pregunta_id, datos)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Eliminar pregunta ────────────────────────────────────────────────────────


@router.delete("/preguntas/{pregunta_id}")
async def eliminar(
    pregunta_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    try:
        return await eliminar_pregunta(db, pregunta_id)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Carga masiva desde CSV/Excel ─────────────────────────────────────────────

MAX_CARGA_MASIVA_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/preguntas/carga-masiva", response_model=ResultadoCargaMasiva)
async def carga_masiva(
    archivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    extensiones_validas = (".csv", ".xlsx", ".xls")
    if not archivo.filename.lower().endswith(extensiones_validas):
        raise HTTPException(
            status_code=400, detail="Solo se aceptan archivos CSV o Excel (.xlsx, .xls)"
        )

    contenido = await archivo.read()
    if len(contenido) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(contenido) > MAX_CARGA_MASIVA_BYTES:
        raise HTTPException(status_code=413, detail="El archivo no puede superar 10 MB")

    try:
        resultado = await cargar_preguntas_csv(
            db, admin.id, contenido, archivo.filename
        )
    except Exception:
        logger.exception("Error procesando carga masiva (admin_id=%s, archivo=%s)", admin.id, archivo.filename)
        raise HTTPException(
            status_code=500, detail="Error procesando el archivo. Revisa el formato e intenta de nuevo."
        )

    return resultado
