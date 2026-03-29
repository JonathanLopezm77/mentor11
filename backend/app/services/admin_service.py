"""
app/services/admin_service.py
Lógica de negocio para el panel de administración de contenido.
CRUD completo de preguntas + carga masiva desde CSV/Excel.
"""
import io
import csv
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contenido import Materia, Pregunta, Respuesta, Pista, NivelDificultad, TipoPregunta
from app.schemas.admin import PreguntaCrear, PreguntaEditar


class AdminError(Exception):
    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _formatear_pregunta(p: Pregunta) -> dict:
    letras = ["A", "B", "C", "D"]
    return {
        "id": p.id,
        "materia_id": p.materia_id,
        "materia_nombre": p.materia.nombre if p.materia else "—",
        "enunciado": p.enunciado,
        "tipo": p.tipo,
        "nivel_dificultad": p.nivel_dificultad,
        "competencia": p.competencia,
        "explicacion_texto": p.explicacion_texto,
        "esta_activa": p.esta_activa,
        "veces_respondida": p.veces_respondida,
        "veces_incorrecta": p.veces_incorrecta,
        "opciones": [
            {"id": o.id, "letra": letras[i], "texto": o.texto, "es_correcta": o.es_correcta}
            for i, o in enumerate(p.respuestas)
        ],
        "pista": p.pistas[0].texto_pista if p.pistas else None,
    }


async def _cargar_pregunta_completa(db: AsyncSession, pregunta_id: int) -> Pregunta:
    resultado = await db.execute(
        select(Pregunta)
        .options(
            selectinload(Pregunta.respuestas),
            selectinload(Pregunta.pistas),
            selectinload(Pregunta.materia),
        )
        .where(Pregunta.id == pregunta_id)
    )
    return resultado.scalar_one_or_none()


# ─── Crear pregunta individual ────────────────────────────────────────────────

async def crear_pregunta(
    db: AsyncSession,
    admin_id: int,
    datos: PreguntaCrear,
) -> dict:
    resultado = await db.execute(select(Materia).where(Materia.id == datos.materia_id))
    if not resultado.scalar_one_or_none():
        raise AdminError("Materia no encontrada", 404)

    pregunta = Pregunta(
        materia_id=datos.materia_id,
        creada_por=admin_id,
        enunciado=datos.enunciado,
        tipo=datos.tipo,
        nivel_dificultad=datos.nivel_dificultad,
        competencia=datos.competencia,
        explicacion_texto=datos.explicacion_texto,
    )
    db.add(pregunta)
    await db.flush()

    for opcion_datos in datos.opciones:
        db.add(Respuesta(
            pregunta_id=pregunta.id,
            texto=opcion_datos.texto,
            es_correcta=opcion_datos.es_correcta,
        ))

    if datos.pista:
        db.add(Pista(pregunta_id=pregunta.id, texto_pista=datos.pista, orden=1))

    await db.commit()
    p = await _cargar_pregunta_completa(db, pregunta.id)
    return _formatear_pregunta(p)


# ─── Listar preguntas ─────────────────────────────────────────────────────────

async def listar_preguntas(
    db: AsyncSession,
    materia_id: int | None = None,
    nivel: str | None = None,
    activa: bool | None = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> dict:
    query = select(Pregunta).options(
        selectinload(Pregunta.materia),
        selectinload(Pregunta.respuestas),
    )

    if materia_id:
        query = query.where(Pregunta.materia_id == materia_id)
    if nivel:
        query = query.where(Pregunta.nivel_dificultad == nivel)
    if activa is not None:
        query = query.where(Pregunta.esta_activa == activa)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    offset = (pagina - 1) * por_pagina
    resultado = await db.execute(query.order_by(Pregunta.id.desc()).offset(offset).limit(por_pagina))
    preguntas = resultado.scalars().all()

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "preguntas": [
            {
                "id": p.id,
                "materia_nombre": p.materia.nombre if p.materia else "—",
                "enunciado": p.enunciado[:100] + "..." if len(p.enunciado) > 100 else p.enunciado,
                "nivel_dificultad": p.nivel_dificultad,
                "tipo": p.tipo,
                "esta_activa": p.esta_activa,
                "veces_respondida": p.veces_respondida,
            }
            for p in preguntas
        ],
    }


# ─── Obtener pregunta por ID ──────────────────────────────────────────────────

async def obtener_pregunta(db: AsyncSession, pregunta_id: int) -> dict:
    p = await _cargar_pregunta_completa(db, pregunta_id)
    if not p:
        raise AdminError("Pregunta no encontrada", 404)
    return _formatear_pregunta(p)


# ─── Editar pregunta ──────────────────────────────────────────────────────────

async def editar_pregunta(db: AsyncSession, pregunta_id: int, datos: PreguntaEditar) -> dict:
    p = await _cargar_pregunta_completa(db, pregunta_id)
    if not p:
        raise AdminError("Pregunta no encontrada", 404)

    if datos.enunciado is not None:
        p.enunciado = datos.enunciado
    if datos.tipo is not None:
        p.tipo = datos.tipo
    if datos.nivel_dificultad is not None:
        p.nivel_dificultad = datos.nivel_dificultad
    if datos.competencia is not None:
        p.competencia = datos.competencia
    if datos.explicacion_texto is not None:
        p.explicacion_texto = datos.explicacion_texto
    if datos.esta_activa is not None:
        p.esta_activa = datos.esta_activa

    if datos.opciones is not None:
        for opcion in list(p.respuestas):
            await db.delete(opcion)
        await db.flush()
        for opcion_datos in datos.opciones:
            db.add(Respuesta(
                pregunta_id=p.id,
                texto=opcion_datos.texto,
                es_correcta=opcion_datos.es_correcta,
            ))

    if datos.pista is not None:
        for pista in list(p.pistas):
            await db.delete(pista)
        await db.flush()
        if datos.pista:
            db.add(Pista(pregunta_id=p.id, texto_pista=datos.pista, orden=1))

    await db.commit()
    p = await _cargar_pregunta_completa(db, pregunta_id)
    return _formatear_pregunta(p)


# ─── Eliminar pregunta ────────────────────────────────────────────────────────

async def eliminar_pregunta(db: AsyncSession, pregunta_id: int) -> dict:
    p = await _cargar_pregunta_completa(db, pregunta_id)
    if not p:
        raise AdminError("Pregunta no encontrada", 404)
    await db.delete(p)
    await db.commit()
    return {"mensaje": f"Pregunta {pregunta_id} eliminada correctamente"}


# ─── Carga masiva desde CSV/Excel ─────────────────────────────────────────────

async def cargar_preguntas_csv(
    db: AsyncSession,
    admin_id: int,
    contenido: bytes,
    nombre_archivo: str,
) -> dict:
    """
    Procesa un archivo CSV o Excel con preguntas y las inserta en la BD.
    Omite preguntas duplicadas (mismo enunciado + misma materia).

    Formato esperado (con encabezados):
    materia_codigo | enunciado | nivel | opcion_a | opcion_b | opcion_c | opcion_d | correcta | explicacion | pista

    - materia_codigo: LC, MAT, SOC, CN, ING
    - nivel: facil, medio, dificil
    - correcta: A, B, C o D
    - explicacion y pista: opcionales
    """
    errores = []
    exitosas = 0

    resultado = await db.execute(select(Materia))
    materias = {m.codigo_icfes: m.id for m in resultado.scalars().all()}

    es_excel = nombre_archivo.lower().endswith(('.xlsx', '.xls'))

    if es_excel:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(contenido))
            ws = wb.active
            filas = []
            headers = None
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(c).strip().lower() if c else "" for c in row]
                else:
                    if any(c is not None for c in row):
                        filas.append(dict(zip(headers, [str(c).strip() if c is not None else "" for c in row])))
        except ImportError:
            return {
                "total_procesadas": 0,
                "total_exitosas": 0,
                "total_fallidas": 0,
                "errores": ["Para procesar archivos Excel instala: pip install openpyxl"],
            }
    else:
        texto = contenido.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(texto))
        filas = [
            {k.strip().lower(): v.strip() for k, v in fila.items()}
            for fila in reader
        ]

    total = len(filas)

    for i, fila in enumerate(filas, start=2):
        fila_num = f"Fila {i}"
        try:
            codigo      = fila.get("materia_codigo", "").upper()
            enunciado   = fila.get("enunciado", "").strip()
            nivel_str   = fila.get("nivel", "medio").strip().lower()
            opcion_a    = fila.get("opcion_a", "").strip()
            opcion_b    = fila.get("opcion_b", "").strip()
            opcion_c    = fila.get("opcion_c", "").strip()
            opcion_d    = fila.get("opcion_d", "").strip()
            correcta    = fila.get("correcta", "").strip().upper()
            explicacion = fila.get("explicacion", "").strip() or None
            pista       = fila.get("pista", "").strip() or None

            if not enunciado:
                errores.append(f"{fila_num}: enunciado vacío")
                continue
            if codigo not in materias:
                errores.append(f"{fila_num}: materia_codigo '{codigo}' no válido. Usar: {list(materias.keys())}")
                continue
            if nivel_str not in ("facil", "medio", "dificil"):
                errores.append(f"{fila_num}: nivel '{nivel_str}' no válido. Usar: facil, medio, dificil")
                continue
            if not opcion_a or not opcion_b:
                errores.append(f"{fila_num}: se requieren al menos opcion_a y opcion_b")
                continue
            if correcta not in ("A", "B", "C", "D"):
                errores.append(f"{fila_num}: correcta '{correcta}' no válido. Usar: A, B, C o D")
                continue

            existente = await db.execute(
                select(Pregunta).where(
                    Pregunta.enunciado == enunciado,
                    Pregunta.materia_id == materias[codigo],
                )
            )
            if existente.scalar_one_or_none():
                errores.append(f"{fila_num}: omitida — ya existe una pregunta con ese enunciado en esa materia")
                continue

            nivel_enum = NivelDificultad(nivel_str)
            pregunta = Pregunta(
                materia_id=materias[codigo],
                creada_por=admin_id,
                enunciado=enunciado,
                tipo=TipoPregunta.opcion_multiple,
                nivel_dificultad=nivel_enum,
                explicacion_texto=explicacion,
            )
            db.add(pregunta)
            await db.flush()

            opciones_texto = {"A": opcion_a, "B": opcion_b, "C": opcion_c, "D": opcion_d}
            for letra, texto in opciones_texto.items():
                if texto:
                    db.add(Respuesta(
                        pregunta_id=pregunta.id,
                        texto=texto,
                        es_correcta=(letra == correcta),
                    ))

            if pista:
                db.add(Pista(pregunta_id=pregunta.id, texto_pista=pista, orden=1))

            exitosas += 1

        except Exception as e:
            errores.append(f"{fila_num}: error inesperado — {str(e)}")

    await db.commit()

    return {
        "total_procesadas": total,
        "total_exitosas": exitosas,
        "total_fallidas": total - exitosas,
        "errores": errores,
    }
