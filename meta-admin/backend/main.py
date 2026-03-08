from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.models import Tenant  # noqa: F401 — registra la tabla
from backend.routers import auth as auth_router
from backend.routers import stats as stats_router
from backend.routers import tenants as tenants_router

# Crear tablas al arrancar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="School-Matz Meta-Admin",
    description="API de meta-administración multitenant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(tenants_router.router, prefix="/api/v1")
app.include_router(stats_router.router, prefix="/api/v1")

# ── Frontend estático ─────────────────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
