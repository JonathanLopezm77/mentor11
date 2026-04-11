"""
app/api/v1/endpoints/admin.py
Endpoints del panel de administración.
Solo accesibles con rol admin_tech.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin, get_db
from app.models.usuario import Usuario
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

    try:
        nombre = f"pregunta_{uuid.uuid4().hex[:8]}"
        url = await subir_imagen(contenido, nombre)
        return {"imagen_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")


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

    try:
        resultado = await cargar_preguntas_csv(
            db, admin.id, contenido, archivo.filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error procesando el archivo: {str(e)}"
        )

    return resultado
