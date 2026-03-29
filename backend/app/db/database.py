"""
app/db/database.py
Configuración de la conexión async a PostgreSQL con SQLAlchemy 2.0.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Motor async — maneja el pool de conexiones
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # Imprime SQL en consola en modo desarrollo
    pool_size=10,              # Conexiones activas en el pool
    max_overflow=20,           # Conexiones extra permitidas en picos
    pool_pre_ping=True,        # Verifica que la conexión siga viva antes de usarla
)

# Fábrica de sesiones async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Evita queries extra al acceder a objetos tras commit
)


# ─── Base para todos los modelos ──────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Clase base que heredan todos los modelos SQLAlchemy.
    Al importar todos los modelos antes de correr Alembic,
    este metadata contiene todas las tablas para las migraciones.
    """
    pass


# ─── Dependencia FastAPI ──────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """
    Generador de sesión de base de datos para inyección de dependencias.

    Uso en un endpoint:
        async def mi_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
