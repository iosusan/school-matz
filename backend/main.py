from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session as DBSession

from backend.database import Base, engine
from backend.models import AdminUser  # noqa: F401 — ensures table is registered
from backend.routers import auth as auth_router
from backend.routers import categorias, material, movimientos, usuarios

# Crear tablas al arrancar
Base.metadata.create_all(bind=engine)


# Migración DDL: añadir columna codigo_qr si no existe
def _add_codigo_qr_column():
    with engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(usuarios)")]
        if "codigo_qr" not in cols:
            conn.exec_driver_sql("ALTER TABLE usuarios ADD COLUMN codigo_qr VARCHAR")
            conn.commit()


_add_codigo_qr_column()


# Migración: regenerar QRs de usuarios que aún tienen código legible (USR-XXXXX o NULL)
# tras el cambio a UUID4 hasheado.
def _migrate_qr_to_uuid4():
    import uuid

    from backend.auth import hash_password
    from backend.models.usuario import Usuario
    from backend.services.qr_service import generate_qr_usuario

    with DBSession(engine) as db:
        # Un hash bcrypt empieza siempre por "$2b$" — si no, es un código antiguo
        usuarios_a_migrar = (
            db.query(Usuario)
            .filter((Usuario.codigo_qr.is_(None)) | (~Usuario.codigo_qr.like("$2b$%")))
            .all()
        )
        for u in usuarios_a_migrar:
            token = str(uuid.uuid4())
            u.codigo_qr = hash_password(token)
            db.flush()
            generate_qr_usuario(u.id, token, u.nombre, u.apellido)
        if usuarios_a_migrar:
            db.commit()


_migrate_qr_to_uuid4()

app = FastAPI(title="School Assets", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(categorias.router, prefix="/api/v1")
app.include_router(material.router, prefix="/api/v1")
app.include_router(movimientos.router, prefix="/api/v1")

# Servir imágenes QR generadas
Path("static/qr").mkdir(parents=True, exist_ok=True)
Path("static/qr_usuarios").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir el frontend (debe ir al final para no solapar las rutas /api)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
