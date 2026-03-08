from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.database import get_db
from backend.models import Tenant
from services.tenant_stats import TenantStats

router = APIRouter(prefix="/tenants", tags=["stats"])

AdminDep = Annotated[str, Depends(get_current_admin)]
DBDep = Annotated[Session, Depends(get_db)]


class StatsOut(BaseModel):
    slug: str
    usuarios_activos: int
    items_material: int
    movimientos_30d: int
    ultimo_movimiento: str | None  # ISO datetime string o None


@router.get("/{slug}/stats", response_model=StatsOut)
def stats_tenant(slug: str, db: DBDep, _: AdminDep):
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    try:
        stats = TenantStats(slug).get()
    except FileNotFoundError:
        # La DB del tenant aún no existe (tenant recién creado o sin datos)
        stats = {
            "usuarios_activos": 0,
            "items_material": 0,
            "movimientos_30d": 0,
            "ultimo_movimiento": None,
        }
    return StatsOut(slug=slug, **stats)
