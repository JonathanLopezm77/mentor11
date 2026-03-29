"""
seed_usuarios.py
Inserta únicamente los usuarios de prueba en la BD.
Ejecutar desde la carpeta backend:
    python seed_usuarios.py
"""
import asyncio

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.usuario import Usuario, Avatar, RolUsuario


async def main():
    print("\n👤 Insertando usuarios de prueba...\n")

    async with AsyncSessionLocal() as session:
        try:
            usuarios = [
                Usuario(
                    username="admin",
                    email="admin@mentor11.co",
                    password_hash=hash_password("Admin123!"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="profesor_demo",
                    email="profesor@mentor11.co",
                    password_hash=hash_password("Profesor123!"),
                    rol=RolUsuario.profesor,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=500,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="estudiante_demo",
                    email="estudiante@mentor11.co",
                    password_hash=hash_password("Estudiante123!"),
                    rol=RolUsuario.estudiante,
                    es_premium=False,
                    esta_activo=True,
                    puntos_totales=1200,
                    racha_actual=3,
                    racha_maxima=7,
                ),
            ]
            session.add_all(usuarios)
            await session.flush()

            avatares = [
                Avatar(usuario_id=usuarios[0].id, animal_base="tigre",  color_primario="#FF6B00"),
                Avatar(usuario_id=usuarios[1].id, animal_base="aguila", color_primario="#2A5FD4"),
                Avatar(usuario_id=usuarios[2].id, animal_base="zorro",  color_primario="#27AE60"),
            ]
            session.add_all(avatares)

            await session.commit()

            print("✅ Usuarios creados exitosamente\n")
            print("─" * 40)
            print("  admin            /  Admin123!")
            print("  profesor_demo    /  Profesor123!")
            print("  estudiante_demo  /  Estudiante123!")
            print("─" * 40)

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
