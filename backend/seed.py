"""
seed.py
Script para poblar la base de datos con las 5 materias del ICFES
y preguntas de ejemplo para probar el modo libre.

Ejecutar con:
    python seed.py
"""

import asyncio
import sys
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Fix emoji output on Windows terminals that use cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.db.database import AsyncSessionLocal
from app.models.contenido import (
    Materia,
    Pregunta,
    Respuesta,
    Pista,
    TipoPregunta,
    NivelDificultad,
)


# ─── Datos de las 5 materias ICFES ───────────────────────────────────────────

MATERIAS = [
    {
        "nombre": "Lectura Crítica",
        "codigo_icfes": "LC",
        "descripcion": "Comprensión e interpretación de textos escritos.",
        "color_hex": "#E74C3C",
    },
    {
        "nombre": "Matemáticas",
        "codigo_icfes": "MAT",
        "descripcion": "Razonamiento lógico y resolución de problemas matemáticos.",
        "color_hex": "#3498DB",
    },
    {
        "nombre": "Sociales y Ciudadanas",
        "codigo_icfes": "SOC",
        "descripcion": "Historia, geografía, política y competencias ciudadanas.",
        "color_hex": "#27AE60",
    },
    {
        "nombre": "Ciencias Naturales",
        "codigo_icfes": "CN",
        "descripcion": "Física, química y biología.",
        "color_hex": "#8E44AD",
    },
    {
        "nombre": "Inglés",
        "codigo_icfes": "ING",
        "descripcion": "Comprensión de lectura y vocabulario en inglés.",
        "color_hex": "#F39C12",
    },
]


# ─── Preguntas de ejemplo por materia ────────────────────────────────────────

PREGUNTAS = [
    # ── Lectura Crítica ───────────────────────────────────────────────────────
    {
        "materia": "LC",
        "tipo": TipoPregunta.lectura_critica,
        "nivel": NivelDificultad.facil,
        "enunciado": 'Lee el siguiente fragmento:\n\n"El ser humano es el único animal que tropieza dos veces con la misma piedra, pero también el único capaz de aprender de sus errores y transformar su entorno."\n\nSegún el texto, ¿cuál es la idea principal?',
        "opciones": [
            ("A", "El ser humano es inferior a los animales.", False),
            (
                "B",
                "El ser humano comete errores pero tiene capacidad de aprendizaje.",
                True,
            ),
            ("C", "Los animales aprenden más rápido que los humanos.", False),
            ("D", "Tropezar con la misma piedra es algo positivo.", False),
        ],
        "explicacion": "La idea principal combina dos aspectos: la tendencia humana a repetir errores y su capacidad única de aprender y transformar su entorno.",
        "pista": "Busca la idea que resume AMBAS partes del texto, no solo una.",
    },
    {
        "materia": "LC",
        "tipo": TipoPregunta.lectura_critica,
        "nivel": NivelDificultad.medio,
        "enunciado": '"La democracia no es perfecta, pero es el peor sistema de gobierno exceptuando todos los demás que han sido probados."\n\n¿Qué figura retórica utiliza esta frase?',
        "opciones": [
            ("A", "Metáfora", False),
            ("B", "Hipérbole", False),
            ("C", "Paradoja", True),
            ("D", "Símil", False),
        ],
        "explicacion": "Es una paradoja porque afirma algo aparentemente contradictorio: que la democracia es el peor sistema, pero a la vez el mejor disponible.",
        "pista": "Piensa en figuras que presentan ideas contradictorias que encierran una verdad.",
    },
    {
        "materia": "LC",
        "tipo": TipoPregunta.lectura_critica,
        "nivel": NivelDificultad.dificil,
        "enunciado": "En un texto argumentativo, ¿cuál es la función principal de los conectores adversativos como 'sin embargo', 'no obstante' y 'aunque'?",
        "opciones": [
            ("A", "Introducir ejemplos que apoyan la tesis.", False),
            ("B", "Indicar consecuencias de una acción.", False),
            (
                "C",
                "Presentar una idea que contrasta o limita la afirmación anterior.",
                True,
            ),
            ("D", "Concluir el argumento principal.", False),
        ],
        "explicacion": "Los conectores adversativos introducen una idea que se opone o matiza lo dicho antes, creando contraste en el argumento.",
        "pista": "¿Qué pasa cuando usas 'sin embargo'? ¿Continúas o cambias de dirección?",
    },
    # ── Matemáticas ───────────────────────────────────────────────────────────
    {
        "materia": "MAT",
        "tipo": TipoPregunta.matematica,
        "nivel": NivelDificultad.facil,
        "enunciado": "Si f(x) = 2x² - 3x + 1, ¿cuánto es f(2)?",
        "opciones": [
            ("A", "3", True),
            ("B", "5", False),
            ("C", "7", False),
            ("D", "1", False),
        ],
        "explicacion": "f(2) = 2(2)² - 3(2) + 1 = 2(4) - 6 + 1 = 8 - 6 + 1 = 3",
        "pista": "Reemplaza x por 2 en la función y resuelve paso a paso respetando el orden de operaciones.",
    },
    {
        "materia": "MAT",
        "tipo": TipoPregunta.matematica,
        "nivel": NivelDificultad.medio,
        "enunciado": "¿Cuál es la pendiente de la recta que pasa por los puntos A(1, 3) y B(4, 9)?",
        "opciones": [
            ("A", "1", False),
            ("B", "2", True),
            ("C", "3", False),
            ("D", "6", False),
        ],
        "explicacion": "Pendiente m = (y₂ - y₁) / (x₂ - x₁) = (9 - 3) / (4 - 1) = 6 / 3 = 2",
        "pista": "La fórmula de la pendiente es m = (y₂ - y₁) / (x₂ - x₁).",
    },
    {
        "materia": "MAT",
        "tipo": TipoPregunta.matematica,
        "nivel": NivelDificultad.medio,
        "enunciado": "Un triángulo rectángulo tiene catetos de 6 cm y 8 cm. ¿Cuánto mide la hipotenusa?",
        "opciones": [
            ("A", "12 cm", False),
            ("B", "14 cm", False),
            ("C", "10 cm", True),
            ("D", "7 cm", False),
        ],
        "explicacion": "Por el teorema de Pitágoras: h² = 6² + 8² = 36 + 64 = 100, entonces h = √100 = 10 cm.",
        "pista": "Usa el teorema de Pitágoras: hipotenusa² = cateto₁² + cateto₂²",
    },
    {
        "materia": "MAT",
        "tipo": TipoPregunta.matematica,
        "nivel": NivelDificultad.dificil,
        "enunciado": "¿Cuál es el valor de x en la ecuación log₂(x) + log₂(x-2) = 3?",
        "opciones": [
            ("A", "x = 4", True),
            ("B", "x = 6", False),
            ("C", "x = 2", False),
            ("D", "x = 8", False),
        ],
        "explicacion": "log₂(x(x-2)) = 3 → x(x-2) = 8 → x² - 2x - 8 = 0 → (x-4)(x+2) = 0. Como x > 2, x = 4.",
        "pista": "Usa la propiedad log(a) + log(b) = log(a·b), luego convierte a forma exponencial.",
    },
    # ── Sociales y Ciudadanas ─────────────────────────────────────────────────
    {
        "materia": "SOC",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.facil,
        "enunciado": "¿En qué año se promulgó la Constitución Política de Colombia que rige actualmente?",
        "opciones": [
            ("A", "1886", False),
            ("B", "1991", True),
            ("C", "1975", False),
            ("D", "2000", False),
        ],
        "explicacion": "La Constitución Política de Colombia vigente fue promulgada el 4 de julio de 1991, reemplazando la Constitución de 1886.",
        "pista": "Ocurrió a principios de la década de los 90.",
    },
    {
        "materia": "SOC",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.medio,
        "enunciado": "¿Cuál de los siguientes es un mecanismo de participación ciudadana consagrado en la Constitución de 1991?",
        "opciones": [
            ("A", "El voto obligatorio", False),
            ("B", "El referendo", True),
            ("C", "La monarquía constitucional", False),
            ("D", "El veto presidencial", False),
        ],
        "explicacion": "El referendo es uno de los mecanismos de participación ciudadana directa establecidos en el Artículo 103 de la Constitución de 1991.",
        "pista": "Piensa en mecanismos donde los ciudadanos votan directamente sobre una decisión.",
    },
    {
        "materia": "SOC",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.dificil,
        "enunciado": "El proceso de Independencia de Colombia se consolidó principalmente gracias a las campañas libertadoras. ¿Qué batalla marcó definitivamente la independencia de la Nueva Granada?",
        "opciones": [
            ("A", "Batalla de Boyacá (1819)", True),
            ("B", "Batalla de Ayacucho (1824)", False),
            ("C", "Batalla de Carabobo (1821)", False),
            ("D", "Batalla de Pichincha (1822)", False),
        ],
        "explicacion": "La Batalla de Boyacá el 7 de agosto de 1819 fue decisiva para la independencia de la Nueva Granada (hoy Colombia), liderada por Simón Bolívar.",
        "pista": "Ocurrió en 1819 y fue liderada por Simón Bolívar en territorio colombiano.",
    },
    # ── Ciencias Naturales ────────────────────────────────────────────────────
    {
        "materia": "CN",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.facil,
        "enunciado": "¿Cuál es la función principal de los glóbulos rojos (eritrocitos) en el cuerpo humano?",
        "opciones": [
            ("A", "Combatir infecciones", False),
            ("B", "Transportar oxígeno", True),
            ("C", "Regular la temperatura corporal", False),
            ("D", "Producir anticuerpos", False),
        ],
        "explicacion": "Los glóbulos rojos contienen hemoglobina, proteína que se une al oxígeno y lo transporta desde los pulmones hasta los tejidos del cuerpo.",
        "pista": "Piensa en qué componente de la sangre da el color rojo y qué gas es vital para las células.",
    },
    {
        "materia": "CN",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.medio,
        "enunciado": "En la fotosíntesis, ¿cuáles son las materias primas que utiliza la planta?",
        "opciones": [
            ("A", "Oxígeno y glucosa", False),
            ("B", "CO₂ y agua", True),
            ("C", "Nitrógeno y glucosa", False),
            ("D", "Oxígeno y agua", False),
        ],
        "explicacion": "En la fotosíntesis: 6CO₂ + 6H₂O + luz → C₆H₁₂O₆ + 6O₂. Las materias primas son el dióxido de carbono (CO₂) y el agua (H₂O).",
        "pista": "Recuerda la ecuación de la fotosíntesis. ¿Qué entra? ¿Qué sale?",
    },
    {
        "materia": "CN",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.dificil,
        "enunciado": "Un objeto de 2 kg cae libremente desde una altura de 20 m. ¿Con qué velocidad aproximada llega al suelo? (g = 10 m/s²)",
        "opciones": [
            ("A", "10 m/s", False),
            ("B", "20 m/s", True),
            ("C", "40 m/s", False),
            ("D", "200 m/s", False),
        ],
        "explicacion": "Usando v² = 2gh → v² = 2(10)(20) = 400 → v = 20 m/s. La masa no afecta la velocidad de caída libre.",
        "pista": "Usa la fórmula v² = 2gh. La masa no importa en caída libre.",
    },
    # ── Inglés ────────────────────────────────────────────────────────────────
    {
        "materia": "ING",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.facil,
        "enunciado": "Choose the correct option to complete the sentence:\n\n'She _______ to school every day by bus.'",
        "opciones": [
            ("A", "go", False),
            ("B", "goes", True),
            ("C", "going", False),
            ("D", "gone", False),
        ],
        "explicacion": "Con sujetos en tercera persona singular (she, he, it) en presente simple, el verbo lleva -s: 'goes'.",
        "pista": "En presente simple con 'she', el verbo necesita una terminación especial.",
    },
    {
        "materia": "ING",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.medio,
        "enunciado": "Read the text:\n\n'Despite the heavy rain, the students decided to go on the field trip. They had been planning it for weeks and didn't want to cancel.'\n\nWhat does 'despite' mean in this context?",
        "opciones": [
            ("A", "Because of", False),
            ("B", "In addition to", False),
            ("C", "Even though / In spite of", True),
            ("D", "As a result of", False),
        ],
        "explicacion": "'Despite' es una preposición que significa 'a pesar de' o 'aunque', indicando contraste entre dos ideas.",
        "pista": "¿La lluvia impidió el viaje o los estudiantes fueron de todas formas?",
    },
    {
        "materia": "ING",
        "tipo": TipoPregunta.opcion_multiple,
        "nivel": NivelDificultad.dificil,
        "enunciado": "Choose the sentence that is grammatically correct:",
        "opciones": [
            ("A", "If I would have studied, I would have passed.", False),
            ("B", "If I had studied, I would have passed.", True),
            ("C", "If I studied, I would have passed.", False),
            ("D", "If I have studied, I would pass.", False),
        ],
        "explicacion": "El tercer condicional usa: 'If + past perfect, would have + past participle'. Se usa para situaciones hipotéticas en el pasado.",
        "pista": "Estamos hablando de una situación hipotética en el pasado. ¿Qué condicional es ese?",
    },
]


# ─── Función principal ────────────────────────────────────────────────────────


async def seed():
    async with AsyncSessionLocal() as db:
        print("🌱 Iniciando seed de la base de datos...\n")

        # ── Insertar materias ──────────────────────────────────────────────────
        materias_map = {}
        for datos in MATERIAS:
            # Verificar si ya existe
            resultado = await db.execute(
                select(Materia).where(Materia.codigo_icfes == datos["codigo_icfes"])
            )
            materia = resultado.scalar_one_or_none()

            if not materia:
                materia = Materia(**datos)
                db.add(materia)
                await db.flush()
                print(f"  ✅ Materia creada: {datos['nombre']}")
            else:
                print(f"  ⏭️  Materia ya existe: {datos['nombre']}")

            materias_map[datos["codigo_icfes"]] = materia

        await db.commit()

        # Recargar materias para obtener IDs actualizados
        for codigo in materias_map:
            resultado = await db.execute(
                select(Materia).where(Materia.codigo_icfes == codigo)
            )
            materias_map[codigo] = resultado.scalar_one()

        print()

        # ── Insertar preguntas ─────────────────────────────────────────────────
        for datos in PREGUNTAS:
            materia = materias_map[datos["materia"]]

            pregunta = Pregunta(
                materia_id=materia.id,
                enunciado=datos["enunciado"],
                tipo=datos["tipo"],
                nivel_dificultad=datos["nivel"],
                explicacion_texto=datos["explicacion"],
            )
            db.add(pregunta)
            await db.flush()

            # Opciones de respuesta
            for _letra, texto, es_correcta in datos["opciones"]:
                opcion = Respuesta(
                    pregunta_id=pregunta.id,
                    texto=texto,
                    es_correcta=es_correcta,
                )
                db.add(opcion)

            # Pista
            pista = Pista(
                pregunta_id=pregunta.id,
                texto_pista=datos["pista"],
                orden=1,
            )
            db.add(pista)

            print(
                f"  ✅ Pregunta [{datos['materia']}] [{datos['nivel'].value}]: {datos['enunciado'][:60]}..."
            )

        await db.commit()
        print(
            f"\n🎉 Seed completado: {len(MATERIAS)} materias y {len(PREGUNTAS)} preguntas insertadas."
        )


if __name__ == "__main__":
    asyncio.run(seed())