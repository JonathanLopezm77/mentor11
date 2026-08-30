"""
seed_usuarios.py
Inserta los usuarios administradores iniciales en la BD.

La contraseña NUNCA se hardcodea aquí -- se lee de la variable de entorno
SEED_ADMIN_PASSWORD y el script se niega a correr si no está definida o es
demasiado corta. Antes tenía "admin12345678" escrita en texto plano en este
archivo para las 5 cuentas admin_tech, versionada en el repo.

Ejecutar desde la carpeta backend:
    SEED_ADMIN_PASSWORD="una-clave-fuerte-y-unica" python seed_usuarios.py
"""

import asyncio
import os

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.usuario import Usuario, RolUsuario

ADMINS = [
    ("AdminJonny", "adminjonny@mentor1.co"),
    ("AdminCris", "admincris@mentor11.co"),
    ("AdminCarlos", "admincarlos@mentor11.co"),
    ("Adminyesid", "adminyesid@mentor11.co"),
    ("Adminsebas", "adminsebas@mentor11.co"),
]


async def main():
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise SystemExit(
            "Falta SEED_ADMIN_PASSWORD (o tiene menos de 12 caracteres).\n"
            'Ejecuta: SEED_ADMIN_PASSWORD="tu-clave-fuerte" python seed_usuarios.py'
        )

    print("\n👤 Insertando usuarios administradores...\n")

    async with AsyncSessionLocal() as session:
        try:
            password_hash = hash_password(password)
            usuarios = [
                Usuario(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    rol=RolUsuario.admin_tech,
                    es_premium=True,
                    esta_activo=True,
                    puntos_totales=0,
                    racha_actual=0,
                    racha_maxima=0,
                )
                for username, email in ADMINS
            ]
            session.add_all(usuarios)
            await session.commit()

            print("✅ Usuarios creados exitosamente\n")
            print("─" * 40)
            for username, _ in ADMINS:
                print(f"  {username}")
            print("─" * 40)
            print("Contraseña: la que definiste en SEED_ADMIN_PASSWORD (no se imprime aquí).")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
