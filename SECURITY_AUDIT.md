# Auditoría de seguridad — Mentor 11

Fecha: 2026-08-30
Alcance: repositorio completo (`backend/`, `frontend/`), más verificación pasiva contra la instancia real en producción (`https://mentor11-production.up.railway.app`) — solo peticiones GET de solo lectura, sin ejecutar ningún ataque real.

## Resumen ejecutivo

Se encontraron **2 vulnerabilidades críticas**, ambas ya corregidas en el código de esta sesión (no desplegadas todavía):

1. **Cualquiera podía registrarse como administrador** con una sola llamada a la API (`rol: "admin_tech"` en el body del registro, sin ninguna validación del servidor). Ya corregido.
2. **5 contraseñas de administrador hardcodeadas en texto plano** en `backend/seed_usuarios.py`, versionadas en el repositorio. El código ya no las hardcodea — pero si ese script se corrió alguna vez contra la base de datos real, esas cuentas siguen teniendo esa contraseña hasta que se rote manualmente en producción (no se puede hacer desde el código).

Además se corrigieron: exposición pública de la documentación Swagger/Redoc, ausencia total de cabeceras de seguridad HTTP, y una librería JWT (`python-jose`) sin mantenimiento con CVEs conocidos, migrada a `PyJWT`.

Quedan pendientes, documentados con su remediación propuesta pero no implementados en esta sesión por requerir pruebas más extensas o ser decisiones de producto: verificación de email en el registro, invalidación real de sesión en logout, Row Level Security en Postgres, y actualización de Pillow/Starlette (ambos con CVEs conocidos pero que requieren un pase de pruebas dedicado por el tamaño del cambio).

## Inventario

Ver Fase 1 completa en el historial de esta conversación — resumen: 46 endpoints REST + 1 WebSocket, todos protegidos por `get_current_user` salvo los públicos de auth; `get_admin` gatea todo `/admin/*`; sin cookies, JWT vía header `Authorization`; sin RLS en Postgres, aislamiento 100% a nivel de aplicación (verificado consistente donde se revisó).

## Modelo de amenazas

Ver Fase 2 completa en el historial — el camino más corto a admin (antes de esta sesión) era literalmente `POST /registro` con `rol: "admin_tech"`, sin necesitar ninguna cuenta previa. Ya cerrado.

## Hallazgos

### [M11-001] Escalada de privilegios vía el campo `rol` en el registro público
- Severidad: CRÍTICA
- Confianza: CONFIRMADO
- Categoría: OWASP A01:2021 – Broken Access Control
- Ubicación: `backend/app/services/auth_service.py:53` (antes del fix), `backend/app/schemas/usuario.py`
- Descripción: `UsuarioRegistro.rol` se pasaba directo del body del cliente a `Usuario(rol=datos.rol)`, sin restricción del servidor. La UI solo ofrece "estudiante"/"profesor", pero nada impedía llamar a la API directo con cualquier valor del enum, incluido `admin_tech`.
- Evidencia:
  ```python
  # auth_service.py:53 (antes)
  nuevo_usuario = Usuario(..., rol=datos.rol)
  ```
- Cómo se explota: `POST /api/v1/auth/registro` con `{"username":"x","email":"x@x.com","password":"12345678","rol":"admin_tech"}` → cuenta admin instantánea.
- Impacto: acceso total al panel admin (banco de preguntas completo: crear/editar/borrar, subir imágenes, carga masiva).
- Remediación: validador Pydantic que solo permite `estudiante`/`profesor` en el registro público. **Ya aplicado y probado** (`schemas/usuario.py`, tests con roles legítimos y con intentos de escalada, ambos verificados).
- Referencias: CWE-269, OWASP ASVS 4.0 – 4.1.1

### [M11-002] Contraseñas de administrador hardcodeadas en el repositorio
- Severidad: CRÍTICA
- Confianza: CONFIRMADO (el código existe así; PROBABLE que afecte producción — pendiente que el usuario lo confirme)
- Categoría: OWASP A07:2021 – Identification and Authentication Failures / CWE-798
- Ubicación: `backend/seed_usuarios.py` (versión anterior al fix de esta sesión)
- Descripción: 5 cuentas `admin_tech` (`AdminJonny`, `AdminCris`, `AdminCarlos`, `Adminyesid`, `Adminsebas`) con la misma contraseña `admin12345678` hardcodeada en texto plano, presente en el repositorio desde el primer commit.
- Impacto: si esas cuentas existen en producción, cualquiera con acceso de lectura al repo (o cualquiera en internet si el repo es público) tiene admin total.
- Remediación: el script ahora exige `SEED_ADMIN_PASSWORD` por variable de entorno, sin default, con mínimo de 12 caracteres — **ya aplicado y probado** (rechaza correr sin la variable, no imprime la contraseña en consola).
- **Acción pendiente del usuario, no automatizable:** verificar en la base de datos de producción si esas cuentas existen y rotarles la contraseña.
- Referencias: CWE-798, OWASP ASVS 4.0 – 2.1.1

### [M11-003] Swagger/Redoc expuestos públicamente sin restricción
- Severidad: MEDIA · Confianza: CONFIRMADO (verificado en vivo contra producción, `/docs` respondía 200)
- Categoría: OWASP API Security Top 10 – API9:2023 Improper Inventory Management
- Ubicación: `backend/main.py`
- Remediación: `docs_url`/`redoc_url`/`openapi_url` ahora `None` por defecto, solo se activan con `ENABLE_DOCS=true` explícito. **Ya aplicado y probado** (verificado apagado por defecto y encendible a propósito).

### [M11-004] Ausencia total de cabeceras de seguridad HTTP
- Severidad: MEDIA · Confianza: CONFIRMADO (verificado en vivo contra producción — ni Railway las agrega)
- Categoría: OWASP ASVS 4.0 – 14.4
- Ubicación: `backend/main.py`
- Remediación: middleware que agrega `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security` y una `Content-Security-Policy` acotada a los hosts externos reales que usa el frontend (Google Fonts, Cloudinary). **Ya aplicado y probado.**
- Nota: la CSP permite `'unsafe-inline'` en scripts porque todo el frontend usa `<script>` inline (no hay build step) — no protege contra XSS por sí sola, pero sí cierra clickjacking, inyección de `<object>`, secuestro de `<base>` y carga de recursos de hosts no esperados.

### [M11-005] `python-jose` sin mantenimiento, con CVEs sin parche
- Severidad: MEDIA · Confianza: CONFIRMADO (`pip-audit` real: PYSEC-2024-232, PYSEC-2024-233, PYSEC-2025-185 sin versión de fix)
- Ubicación: `backend/app/core/security.py`
- Remediación: migrado a `PyJWT==2.9.0`, misma firma de funciones. **Ya aplicado y probado exhaustivamente**: creación/decodificación de tokens, rechazo de tokens vencidos/manipulados/basura, y — el más importante — confirmé que un token creado por la librería vieja se sigue decodificando bien con la nueva, así que nadie pierde su sesión activa con el deploy.

### [M11-006] `python-multipart` con CVEs conocidos
- Severidad: BAJA · Confianza: CONFIRMADO (`pip-audit`)
- Ubicación: `requirements.txt`
- Remediación: bump de `0.0.9` a `0.0.18`. Uso interno de FastAPI (subida de imágenes/CSV en `/admin`), sin API propia usada por el código de la app — riesgo de regresión bajo. **Ya aplicado.**

### [M11-007] Sin verificación de email en el registro
- Severidad: MEDIA · Confianza: CONFIRMADO
- Descripción: cualquiera se registra con cualquier correo (propio o ajeno) y la cuenta queda operativa de inmediato.
- Remediación propuesta: token de verificación por correo (mismo patrón ya usado en recuperación de contraseña), cuenta con acceso limitado hasta confirmar.
- **No implementado en esta sesión** — es una feature nueva, no un parche, y además cambia el flujo de onboarding que ven los usuarios: te lo dejo para que decidas si lo priorizás.

### [M11-008] Sin invalidación real de sesión en logout
- Severidad: MEDIA · Confianza: CONFIRMADO
- Descripción: JWT stateless sin lista de revocación — "logout" solo borra el token en el navegador; un token robado sigue siendo válido hasta que expira.
- Remediación propuesta: lista de revocación (tabla o cache con jti de tokens invalidados), o migrar el refresh_token a cookie `HttpOnly` con rotación.
- **No implementado** — cambio de arquitectura, requiere decidir el mecanismo y probarlo contra sesiones reales.

### [M11-009] `_requerir_profesor()` es un guard manual, no automático
- Severidad: BAJA · Confianza: CONFIRMADO
- Ubicación: `backend/app/api/v1/endpoints/profesor.py`
- Descripción: hay que llamarlo a mano en cada endpoint nuevo; hoy está bien aplicado en todos los existentes, pero no hay red de seguridad si se olvida en uno futuro.
- Remediación propuesta: convertirlo en una dependencia de FastAPI (`Depends(requerir_profesor)`) reutilizable, igual que `get_admin`.

### [M11-010] Sin Row Level Security en Postgres
- Severidad: BAJA (hoy) · Confianza: CONFIRMADO
- Descripción: todo el aislamiento entre usuarios es a nivel de aplicación. Verificado bien aplicado donde se revisó, pero es un único punto de falla.
- Remediación propuesta: RLS como defensa en profundidad — cambio estructural, no urgente dado que hoy funciona correctamente.

### [M11-011] Pillow 10.4.0 con múltiples CVEs
- Severidad: MEDIA · Confianza: CONFIRMADO (`pip-audit`, +15 avisos)
- Descripción: usado para redimensionar avatares en el modo Online, procesa bytes de imagen potencialmente influenciados por el cliente.
- Remediación propuesta: actualizar a Pillow 12.x — es un salto de versión mayor con cambios de API documentados en su changelog; requiere un pase de pruebas dedicado contra el flujo real de avatares antes de aplicarlo a ciegas.

### [M11-012] Starlette/FastAPI desactualizados
- Severidad: MEDIA · Confianza: CONFIRMADO (`pip-audit`, múltiples CVEs con fix en versiones posteriores)
- Descripción: Starlette es la base de todo el framework — un upgrade toca ruteo, middlewares y WebSockets de la app entera.
- Remediación propuesta: actualizar en una rama aparte con un pase completo de pruebas manuales de los 5 modos de juego, aulas y simulacro antes de fusionar — no es algo para hacer sin poder probarlo contra un navegador real.

### [M11-013] Sin chequeo contra contraseñas filtradas
- Severidad: BAJA — mejora opcional, no urgente.

### [M11-014] Sin logging/observabilidad de intentos de autenticación
- Severidad: BAJA · Ya parcialmente identificado en la auditoría técnica anterior de esta misma sesión (ausencia de logging estructurado en general).

## Zonas no auditadas

- Backups de la base de datos Postgres en Railway (configuración, cifrado, si se han probado restauraciones) — necesito que confirmes esto desde el panel de Railway.
- Configuración exacta de `ALLOWED_ORIGINS` en las variables de entorno reales de Railway.
- Pipeline de CI/CD — no until GitHub Actions ni ningún otro pipeline en el repo; el deploy parece disparar directo desde el push a `main`.
- Explotabilidad exacta de cada uno de los ~48 CVEs reportados por `pip-audit` en Pillow/Starlette — confirmé que existen y tienen versión de fix, pero determinar cuáles son explotables en el uso específico que hace esta app de cada librería requeriría investigación caso por caso que no alcancé a hacer.

## Autocrítica

- **El hallazgo del que tengo menos confianza:** M11-002 (contraseñas del seed) — confirmé al 100% que el código las tiene hardcodeadas, pero no tengo forma de confirmar si esas cuentas existen realmente en la base de datos de producción. Podría ser que nunca se corrió ese script contra producción y el riesgo real sea cero.
- **Qué parte del sistema no entendí bien:** el pipeline de deploy real de Railway — no sé si hay algún paso intermedio (staging, revisión manual) entre un push a `main` y que el cambio esté sirviendo tráfico real.
- **Qué haría un atacante con más tiempo que yo:** probaría cada uno de los CVEs de Pillow/Starlette contra el uso específico de esta app (no me alcanzó el tiempo para verificar explotabilidad caso por caso), y buscaría con más profundidad si hay algún otro campo tipo `rol` en algún otro formulario que se me haya pasado.
- **Si tuviera que apostar por una sola vulnerabilidad que causa el próximo incidente:** sería M11-002 — si esas cuentas existen en producción con esa contraseña, es la más fácil de explotar por alguien que ni siquiera necesita leer código, solo probar una contraseña obvia contra 5 usuarios conocidos.
