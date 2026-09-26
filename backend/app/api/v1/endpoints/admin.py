"""
app/api/v1/endpoints/admin.py
Endpoints del panel de administración.
Solo accesibles con rol admin_tech.
"""

import io
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin, get_db
from app.models.usuario import Usuario
from app.models.sistema import Reporte, EstadoReporte

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
    exportar_preguntas_excel,
    actualizar_desde_excel,
    AdminError,
)
from app.services.imagen_service import subir_imagen

router = APIRouter()


# ─── Reportes de preguntas ────────────────────────────────────────────────────


@router.get("/reportes")
async def listar_reportes(
    estado: str | None = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(30, le=100),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    from sqlalchemy import select as sa_select, func as sa_func
    from sqlalchemy.orm import selectinload

    query = (
        sa_select(Reporte)
        .options(
            selectinload(Reporte.usuario),
            selectinload(Reporte.pregunta),
        )
        .order_by(Reporte.creado_en.desc())
    )
    if estado:
        query = query.where(Reporte.estado == estado)

    total = (await db.execute(sa_select(sa_func.count()).select_from(query.subquery()))).scalar()
    offset = (pagina - 1) * por_pagina
    res = await db.execute(query.offset(offset).limit(por_pagina))
    reportes = res.scalars().all()

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "reportes": [
            {
                "id": r.id,
                "pregunta_id": r.pregunta_id,
                "pregunta_enunciado": (r.pregunta.enunciado[:80] + "..." if r.pregunta and len(r.pregunta.enunciado) > 80 else (r.pregunta.enunciado if r.pregunta else None)),
                "tipo": r.tipo,
                "descripcion": r.descripcion,
                "estado": r.estado,
                "usuario": r.usuario.username if r.usuario else "—",
                "creado_en": r.creado_en.isoformat(),
            }
            for r in reportes
        ],
    }


@router.patch("/reportes/{reporte_id}")
async def actualizar_estado_reporte(
    reporte_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
    estado: str = Query(...),
):
    from sqlalchemy import select as sa_select

    if estado not in [e.value for e in EstadoReporte]:
        raise HTTPException(status_code=400, detail="Estado no válido")

    res = await db.execute(sa_select(Reporte).where(Reporte.id == reporte_id))
    reporte = res.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    reporte.estado = EstadoReporte(estado)
    reporte.resuelto_por = admin.id
    await db.commit()
    return {"mensaje": f"Reporte marcado como {estado}"}


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


# ─── Exportar preguntas para corrección ortográfica ──────────────────────────


@router.get("/preguntas/exportar")
async def exportar_preguntas(
    materia_id: int | None = Query(None, description="Filtrar por materia (opcional)"),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    """
    Exporta todas las preguntas activas a un Excel (.xlsx) listo para
    corrección ortográfica con IA. Incluye columna 'id' para reimportación.
    """
    try:
        contenido = await exportar_preguntas_excel(db, materia_id=materia_id)
    except Exception:
        logger.exception("Error exportando preguntas (admin_id=%s)", admin.id)
        raise HTTPException(status_code=500, detail="Error al generar el archivo de exportación.")

    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=preguntas_mentor11.xlsx"},
    )


# ─── Importar correcciones ortográficas ──────────────────────────────────────


@router.post("/preguntas/actualizar-masivo")
async def actualizar_preguntas_masivo(
    archivo: UploadFile = File(..., description="Excel exportado con correcciones aplicadas"),
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    """
    Recibe el Excel exportado (ya corregido por IA u otro medio) y actualiza
    las preguntas existentes por ID. No crea preguntas nuevas ni elimina
    las que no estén en el archivo.
    """
    if not archivo.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Solo se aceptan archivos Excel (.xlsx, .xls)"
        )

    contenido = await archivo.read()
    if len(contenido) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo no puede superar 10 MB")

    try:
        resultado = await actualizar_desde_excel(db, contenido, archivo.filename)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)
    except Exception:
        logger.exception("Error actualizando preguntas (admin_id=%s)", admin.id)
        raise HTTPException(status_code=500, detail="Error procesando el archivo.")

    return resultado


# ─── Subir imagen ─────────────────────────────────────────────────────────────

MAX_IMAGEN_BYTES = 8 * 1024 * 1024  # 8 MB

_FIRMAS_IMAGEN = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}


def _tipo_imagen_real(contenido: bytes) -> str | None:
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