# Checklist de seguridad pre-deploy — Mentor 11

Usar antes de fusionar cualquier feature nueva a `main`. Basado en los hallazgos reales de la auditoría de 2026-08-30 (`SECURITY_AUDIT.md`) — cada punto existe porque algo similar ya falló acá una vez.

## Autenticación y autorización
- [ ] ¿Algún campo del body de un request de usuario público (registro, edición de perfil) permite que el cliente elija su propio rol, permiso o cualquier campo que decida un privilegio? Si sí, ¿está explícitamente restringido con un validador (no solo un default)?
- [ ] ¿Todo endpoint nuevo que dependa de un rol usa `Depends(get_admin)` o el guard correspondiente, no solo un chequeo manual dentro de la función?
- [ ] ¿Todo endpoint que recibe un `id` en la URL valida que el recurso pertenezca al usuario autenticado (no solo que esté logueado)?

## Secretos y configuración
- [ ] ¿Alguna contraseña, clave o token quedó escrito directo en el código (incluidos scripts de seed/setup)?
- [ ] ¿Hay algún archivo `.env` real (no `.env.example`) a punto de commitearse? (`git status` antes de cada commit)
- [ ] ¿`.env.example` sigue reflejando las variables que el código realmente lee?

## Entrada de datos
- [ ] ¿Todo endpoint POST/PUT tiene un schema Pydantic explícito, sin pasar el body entero a un `update()`/constructor sin lista blanca?
- [ ] ¿Toda subida de archivo valida el contenido real (magic bytes), no solo la extensión, y tiene un tope de tamaño?
- [ ] ¿Todo endpoint público sensible (login, registro, recuperar contraseña) tiene rate limiting?

## Salida de datos
- [ ] ¿Algún dato de usuario se inserta con `innerHTML` sin pasar por una función que escape `<`/`>`/`&` primero?
- [ ] ¿Alguna respuesta de error nueva devuelve `str(exception)` directo al cliente, en vez de loguearlo y devolver un mensaje genérico?
- [ ] ¿Algún endpoint nuevo devuelve más campos de los que el frontend realmente usa (incluyendo `password_hash` u otro dato sensible)?

## Infraestructura
- [ ] Si se toca `main.py`: ¿sigue sin exponerse Swagger/Redoc por defecto (`ENABLE_DOCS`)?
- [ ] Si se agrega una dependencia nueva: ¿se corrió `pip-audit` para confirmar que no trae CVEs conocidos sin parche?
- [ ] Si se agrega un host externo nuevo (CDN, API de terceros): ¿se actualizó la Content-Security-Policy en `main.py` para incluirlo?

## Antes de cada release
- [ ] `pip-audit -r requirements.txt` sin vulnerabilidades de severidad alta/crítica sin revisar.
- [ ] Ninguna migración de Alembic nueva sin su `downgrade()` correspondiente.
- [ ] El arranque completo de la app (`import main`) se probó en un entorno limpio instalando solo `requirements.txt` (así es como corre en Railway).
