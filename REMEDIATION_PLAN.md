# Plan de remediación — Mentor 11

Ver `SECURITY_AUDIT.md` para el detalle completo de cada hallazgo.

## Ya hecho en esta sesión (código local, probado, sin desplegar todavía)

- [x] M11-001 — Registro público ya no permite autoasignarse `admin_tech`/`admin_contenido`.
- [x] M11-002 (parcial) — `seed_usuarios.py` ya no hardcodea contraseñas; exige `SEED_ADMIN_PASSWORD` por entorno.
- [x] M11-003 — Swagger/Redoc apagados por defecto (`ENABLE_DOCS=true` para encenderlos a propósito).
- [x] M11-004 — Cabeceras de seguridad HTTP (CSP, HSTS, X-Frame-Options, etc.) en todas las respuestas.
- [x] M11-005 — Migrado de `python-jose` a `PyJWT`, verificado que no invalida sesiones activas.
- [x] M11-006 — `python-multipart` actualizado.

## Pendiente — acción tuya, no automatizable desde el código

- [ ] **Verificar en la base de datos de producción** si existen las cuentas `AdminJonny`, `AdminCris`, `AdminCarlos`, `Adminyesid`, `Adminsebas` (o cualquier `admin_tech`/`admin_contenido` que no reconozcas).
- [ ] Si existen, **rotar sus contraseñas ya**.
- [ ] Confirmar el valor real de `ALLOWED_ORIGINS` configurado en Railway.
- [ ] Confirmar si Postgres en Railway tiene backups automáticos y si alguna vez se probó restaurar uno.

## Pendiente — quick wins técnicos no implementados (esfuerzo bajo-medio, requieren tu ok)

- [ ] M11-009 — Convertir `_requerir_profesor()` en un `Depends()` reutilizable en vez de un helper manual.
- [ ] M11-013 — Comprobar contraseñas nuevas contra el corpus de HaveIBeenPwned (k-anonymity, no envía la contraseña completa).
- [ ] M11-014 — Logging estructurado mínimo en los puntos de login/registro/recuperación (ya se identificó como necesario en la auditoría técnica anterior).

## Pendiente — estructural (semanas, requiere diseño y pruebas dedicadas)

- [ ] M11-007 — Verificación de email en el registro (decisión de producto: ¿bloquea el uso hasta verificar, o solo limita algunas funciones?).
- [ ] M11-008 — Invalidación real de sesión en logout (decidir mecanismo: lista de revocación vs. cookie httpOnly con rotación).
- [ ] M11-010 — Row Level Security en Postgres como defensa en profundidad.
- [ ] M11-011 — Actualizar Pillow (10.4.0 → 12.x), requiere pase de pruebas del flujo de avatares.
- [ ] M11-012 — Actualizar Starlette/FastAPI, requiere pase de pruebas de toda la app (los 5 modos de juego, aulas, simulacro, WebSocket de Online).

## Orden sugerido si se retoma esto en una próxima sesión

1. Confirmar y cerrar M11-002 en producción (lo único que sigue siendo una emergencia activa potencial).
2. M11-009 (guard de profesor) — bajo esfuerzo, cierra un patrón frágil antes de que crezca.
3. M11-007 (verificación de email) — la funcionalidad pendiente de mayor impacto real, dado que hay menores de edad usando la plataforma.
4. M11-011 y M11-012 (upgrades de dependencias) — juntas, en una rama aparte, con un pase de pruebas manual completo antes de fusionar.
5. M11-008 y M11-010 — cambios de arquitectura, para cuando haya tiempo de diseñarlos con calma.
