"""
app/api/v1/endpoints/admin.py
Endpoints del panel de administración.
Solo accesibles con rol admin_tech.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
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

router = APIRouter()


# ─── Listar preguntas ─────────────────────────────────────────────────────────


@router.get("/preguntas", response_model=PaginacionRespuesta)
async def listar(
    materia_id: int | None = Query(None, description="Filtrar por materia"),
    nivel: str | None = Query(None, description="facil, medio, dificil"),
    activa: bool | None = Query(None, description="True=activas, False=inactivas"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    """Lista todas las preguntas con filtros opcionales y paginación."""
    return await listar_preguntas(db, materia_id, nivel, activa, pagina, por_pagina)


# ─── Descargar plantilla CSV ──────────────────────────────────────────────────


@router.get("/preguntas/plantilla")
async def descargar_plantilla(
    admin: Usuario = Depends(get_admin),
):
    """
    Descarga una plantilla CSV de ejemplo para la carga masiva de preguntas.
    """
    from fastapi.responses import Response

    plantilla = (
        "materia_codigo;enunciado;nivel;opcion_a;opcion_b;opcion_c;opcion_d;correcta;explicacion;pista\n"
        "MAT;¿Cuánto es 2 + 2?;facil;3;4;5;6;B;La suma de 2 + 2 es 4;Piensa en contar con los dedos\n"
        "LC;¿Qué figura retórica es 'el tiempo es oro'?;medio;Metáfora;Hipérbole;Símil;Paradoja;A;"
        "Una metáfora compara sin usar 'como';Piensa en comparaciones directas\n"
        "ING;Choose the correct verb: She ___ to school;facil;go;goes;going;gone;B;"
        "Third person singular uses -s;Think about he/she/it\n"
    )

    return Response(
        content=plantilla.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_preguntas.csv"},
    )


# ─── Ver detalle de una pregunta ──────────────────────────────────────────────


@router.get("/preguntas/{pregunta_id}", response_model=PreguntaDetalle)
async def ver_pregunta(
    pregunta_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    """Devuelve el detalle completo de una pregunta con opciones y pista."""
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
    """
    Crea una nueva pregunta con sus opciones y pista opcional.
    Exactamente 1 opción debe tener es_correcta=true.
    """
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
    """
    Edita una pregunta. Solo se actualizan los campos enviados.
    Si envías opciones, reemplaza todas las anteriores.
    """
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
    """Elimina permanentemente una pregunta con todas sus opciones y pistas."""
    try:
        return await eliminar_pregunta(db, pregunta_id)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)


# ─── Carga masiva desde CSV/Excel ─────────────────────────────────────────────


@router.post("/preguntas/carga-masiva", response_model=ResultadoCargaMasiva)
async def carga_masiva(
    archivo: UploadFile = File(..., description="Archivo CSV o Excel (.xlsx)"),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    """
    Carga múltiples preguntas desde un archivo CSV o Excel.

    Formato de columnas requerido:
    | materia_codigo | enunciado | nivel | opcion_a | opcion_b | opcion_c | opcion_d | correcta | explicacion | pista |

    - materia_codigo: LC, MAT, SOC, CN, ING
    - nivel: facil, medio, dificil
    - correcta: A, B, C o D
    - explicacion y pista: opcionales

    Descarga la plantilla de ejemplo desde GET /admin/preguntas/plantilla
    """
    extensiones_validas = (".csv", ".xlsx", ".xls")
    if not archivo.filename.lower().endswith(extensiones_validas):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan archivos CSV o Excel (.xlsx, .xls)",
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
