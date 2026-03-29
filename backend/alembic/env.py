"""
alembic/env.py
Configuración de Alembic para migraciones — usa conexión sync (psycopg2).
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Importar configuración y modelos ────────────────────────────────────────
from app.core.config import settings
from app.db.database import Base
import app.models  # noqa: F401 — importa todos los modelos para que Alembic los detecte

# Configuración de Alembic
config = context.config

# Inyectar la URL sync desde nuestro .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Modo offline (genera SQL sin conectar a la BD) ───────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Modo online (conecta a la BD y aplica cambios) ───────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": settings.DATABASE_URL_SYNC},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
