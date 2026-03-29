# Mentor 11

Plataforma gamificada de preparación para el ICFES Saber 11.

## Stack tecnológico

| Capa          | Tecnología                          |
|---------------|-------------------------------------|
| Backend       | Python 3.11+ · FastAPI              |
| ORM           | SQLAlchemy 2.0 (async)              |
| Migraciones   | Alembic                             |
| Base de datos | PostgreSQL 15                       |
| Autenticación | JWT (python-jose) + bcrypt          |
| Frontend      | HTML · CSS · JavaScript (vanilla)   |

## Estructura del proyecto

```
mentor11/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Rutas de la API REST
│   │   ├── core/               # Config, seguridad, JWT
│   │   ├── db/                 # Conexión y sesión de BD
│   │   ├── models/             # Modelos SQLAlchemy (tablas)
│   │   ├── schemas/            # Esquemas Pydantic (validación)
│   │   └── services/           # Lógica de negocio
│   ├── alembic/                # Migraciones de BD
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── seed.py                 # Inserta materias y preguntas de ejemplo
│   ├── seed_usuarios.py        # Inserta usuarios de prueba
│   ├── requirements.txt
│   └── .env.example
└── frontend/                   # HTML/CSS/JS servido por FastAPI
```

## Requisitos previos

- Python 3.11 o superior
- PostgreSQL 15 instalado y corriendo
- La base de datos `mentor` debe existir antes de continuar

Verificar el puerto de PostgreSQL (por defecto es **5432**):
```sql
-- En psql o pgAdmin:
SHOW port;
```

Crear la base de datos:
```sql
CREATE DATABASE mentor;
```

---

## Instalación paso a paso

> Todos los comandos se ejecutan desde la carpeta `backend/`.

### 1. Entrar a la carpeta del backend

```bash
cd backend
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv
```

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux / Mac:**
```bash
source venv/bin/activate
```

> Si PowerShell bloquea la activación, ejecuta primero:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno




### 5. Crear las tablas (migraciones)

```bash
alembic upgrade head
```

Deberías ver algo como:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 13e85a652e62, init
INFO  [alembic.runtime.migration] Running upgrade 13e85a652e62 -> 672633936a1e, add_textos_fix_preguntas
```

### 6. Poblar la base de datos con datos iniciales

```bash
python seed.py
python seed_usuarios.py
```

Resultado esperado de `seed.py`:
```
🌱 Iniciando seed de la base de datos...
  ✅ Materia creada: Lectura Crítica
  ...
🎉 Seed completado: 5 materias y 16 preguntas insertadas.
```

Usuarios de prueba creados por `seed_usuarios.py`:

| Usuario           | Contraseña        | Rol          |
|-------------------|-------------------|--------------|
| `admin`           | `Admin123!`       | `admin_tech` |
| `estudiante_demo` | `Estudiante123!`  | `estudiante` |

### 7. Levantar el servidor

```bash
uvicorn main:app --reload
```

Abrir en el navegador: **http://localhost:8000**
Documentación de la API: **http://localhost:8000/docs**

---

## Notas importantes

- El frontend (HTML/CSS/JS) es servido directamente por FastAPI desde la carpeta `frontend/`. No requiere npm ni Node.js.
- Cada vez que reinicias el PC debes volver a activar el entorno virtual (paso 2) antes de correr el servidor.
- Para evitar problemas de caché del navegador usa `Ctrl + Shift + R` (hard refresh).
- **Windows — problemas con emojis en la terminal:** si `seed.py` falla con `UnicodeEncodeError`, establece la variable de entorno antes de correrlo:
  ```powershell
  $env:PYTHONUTF8 = "1"
  python seed.py
  ```
