import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.config import settings
from backend.database import get_db
from backend.models import Tenant
from services.docker_service import DockerService

router = APIRouter(prefix="/tenants", tags=["tenants"])

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")

AdminDep = Annotated[str, Depends(get_current_admin)]
DBDep = Annotated[Session, Depends(get_db)]


# ── Schemas ───────────────────────────────────────────────────


class TenantCreate(BaseModel):
    slug: str
    nombre: str
    admin_username: str
    admin_password: str

    @field_validator("slug")
    @classmethod
    def slug_valido(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(
                "slug solo puede contener letras minúsculas, números y guiones, "
                "entre 3 y 64 caracteres, sin empezar ni terminar en guión"
            )
        return v


class TenantOut(BaseModel):
    id: int
    slug: str
    nombre: str
    base_domain: str
    admin_username: str
    estado: str
    created_at: datetime
    last_activity: datetime | None

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────


@router.get("", response_model=list[TenantOut])
def listar_tenants(db: DBDep, _: AdminDep):
    return db.query(Tenant).order_by(Tenant.created_at.desc()).all()


@router.get("/{slug}", response_model=TenantOut)
def obtener_tenant(slug: str, db: DBDep, _: AdminDep):
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


@router.post("", response_model=TenantOut, status_code=201)
def crear_tenant(body: TenantCreate, db: DBDep, _: AdminDep):
    if db.query(Tenant).filter(Tenant.slug == body.slug).first():
        raise HTTPException(status_code=409, detail="Ya existe un tenant con ese slug")

    tenant = Tenant(
        slug=body.slug,
        nombre=body.nombre,
        base_domain=settings.base_domain,
        admin_username=body.admin_username,
        estado="creating",
        created_at=datetime.utcnow(),
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    try:
        svc = DockerService()
        svc.deploy(
            slug=body.slug,
            base_domain=settings.base_domain,
            admin_username=body.admin_username,
            admin_password=body.admin_password,
        )
        tenant.estado = "running"
    except Exception as exc:
        tenant.estado = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error desplegando tenant: {exc}") from exc

    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{slug}/start", response_model=TenantOut)
def iniciar_tenant(slug: str, db: DBDep, _: AdminDep):
    tenant = _get_or_404(slug, db)
    try:
        DockerService().start(slug)
        tenant.estado = "running"
        db.commit()
        db.refresh(tenant)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return tenant


@router.post("/{slug}/stop", response_model=TenantOut)
def detener_tenant(slug: str, db: DBDep, _: AdminDep):
    tenant = _get_or_404(slug, db)
    try:
        DockerService().stop(slug)
        tenant.estado = "stopped"
        db.commit()
        db.refresh(tenant)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return tenant


@router.delete("/{slug}", status_code=204)
def eliminar_tenant(slug: str, db: DBDep, _: AdminDep):
    tenant = _get_or_404(slug, db)
    try:
        DockerService().destroy(slug)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    db.delete(tenant)
    db.commit()


# ── Helpers ───────────────────────────────────────────────────


def _get_or_404(slug: str, db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant
