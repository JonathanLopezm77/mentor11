"""
seed_usuarios.py
Inserta únicamente los usuarios de prueba en la BD.
Ejecutar desde la carpeta backend:
    python seed_usuarios.py
"""

import asyncio

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.usuario import Usuario, RolUsuario


async def main():
    print("\n👤 Insertando usuarios de prueba...\n")

    async with AsyncSessionLocal() as session:
        try:
            usuarios = [
                Usuario(
                    username="AdminJonny",
                    email="adminjonny@mentor1.co",
                    password_hash=hash_password("admin12345678"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="AdminCris",
                    email="admin@mentor11.co",
                    password_hash=hash_password("admin12345678"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="AdminCarlos",
                    email="admincarlos@mentor11.co",
                    password_hash=hash_password("admin12345678"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="Adminyesid",
                    email="adminyesid@mentor11.co",
                    password_hash=hash_password("admin12345678"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
                Usuario(
                    username="Adminsebas",
                    email="admin@mentor11.co",
                    password_hash=hash_password("admin12345678"),
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                ),
            ]
            session.add_all(usuarios)
            await session.commit()

            print("✅ Usuarios creados exitosamente\n")
            print("─" * 40)
            print("  AdminJonny            /  admin12345678")
            print("  AdminCris            /   admin12345678")
            print("─" * 40)

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
