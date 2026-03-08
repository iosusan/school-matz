import contextlib
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models.movimiento import Movimiento
from backend.models.usuario import Usuario
from backend.schemas.movimiento import (
    EntradaRequest,
    EntradaResponse,
    MovimientoOut,
    PrestamoActivo,
    SalidaRequest,
    SalidaResponse,
)
from backend.services.movimiento_service import registrar_entrada, registrar_salida

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.post("/salida", response_model=SalidaResponse)
def salida(
    data: SalidaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    mov = registrar_salida(db, data.codigo_qr, current_user.id, data.notas)
    return SalidaResponse(
        ok=True,
        movimiento_id=mov.id,
        material=mov.material,
        usuario=mov.usuario,
        fecha_hora=mov.fecha_hora,
    )


@router.post("/entrada", response_model=EntradaResponse)
def entrada(
    data: EntradaRequest, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
):
    mov = registrar_entrada(db, data.codigo_qr, data.notas)
    return EntradaResponse(
        ok=True,
        movimiento_id=mov.id,
        material=mov.material,
        usuario=mov.usuario,
        fecha_hora=mov.fecha_hora,
    )


@router.get("/activos", response_model=list[PrestamoActivo])
def prestamos_activos(db: Session = Depends(get_db)):
    from backend.models.material import Material

    materiales_prestados = db.query(Material).filter(Material.estado == "prestado").all()
    result = []
    for mat in materiales_prestados:
        ultimo = (
            db.query(Movimiento)
            .filter(Movimiento.material_id == mat.id, Movimiento.tipo == "salida")
            .order_by(Movimiento.fecha_hora.desc())
            .first()
        )
        if ultimo:
            result.append(
                PrestamoActivo(material=mat, usuario=ultimo.usuario, desde=ultimo.fecha_hora)
            )
    return result


@router.get("", response_model=list[MovimientoOut])
def listar_movimientos(
    usuario_id: int | None = None,
    material_id: int | None = None,
    tipo: str | None = None,
    fecha_desde: str | None = Query(None, description="ISO date: 2025-01-01"),
    fecha_hasta: str | None = Query(None, description="ISO date: 2025-12-31"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(Movimiento)
    if usuario_id:
        q = q.filter(Movimiento.usuario_id == usuario_id)
    if material_id:
        q = q.filter(Movimiento.material_id == material_id)
    if tipo:
        q = q.filter(Movimiento.tipo == tipo)
    if fecha_desde:
        with contextlib.suppress(ValueError):
            q = q.filter(Movimiento.fecha_hora >= datetime.fromisoformat(fecha_desde))
    if fecha_hasta:
        try:
            # incluir todo el día
            hasta = datetime.fromisoformat(fecha_hasta).replace(hour=23, minute=59, second=59)
            q = q.filter(Movimiento.fecha_hora <= hasta)
        except ValueError:
            pass
    return q.order_by(Movimiento.fecha_hora.desc()).limit(limit).all()
