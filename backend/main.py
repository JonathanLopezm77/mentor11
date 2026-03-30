"""
main.py
Punto de entrada de la aplicación Mentor 11 con FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uvicorn

from app.core.config import settings
from app.api.v1.endpoints import auth, juego, admin, perfil

# ─── Crear la aplicación ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API REST para la plataforma de preparación ICFES Saber 11 — Mentor 11",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Autenticación"],
)
app.include_router(
    juego.router,
    prefix=f"{settings.API_V1_PREFIX}/juego",
    tags=["Modo Libre"],
)
app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Panel Admin"],
)
app.include_router(
    perfil.router,
    prefix=f"{settings.API_V1_PREFIX}/perfil",
    tags=["Perfil"],
)


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


# ─── Frontend estático ────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}

    @app.get("/", include_in_schema=False)
    async def serve_login():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=NO_CACHE)

    @app.get("/{page}.html", include_in_schema=False)
    async def serve_page(page: str):
        path = os.path.join(FRONTEND_DIR, f"{page}.html")
        if os.path.exists(path):
            return FileResponse(path, headers=NO_CACHE)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=NO_CACHE)


# ─── Eventos ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    print(
        f"[OK] {settings.PROJECT_NAME} v{settings.VERSION} iniciando en modo {settings.ENVIRONMENT}"
    )


@app.on_event("shutdown")
async def on_shutdown():
    print("[STOP] Servidor detenido correctamente")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
