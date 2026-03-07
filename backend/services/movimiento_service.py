from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.material import Material
from backend.models.movimiento import Movimiento
from backend.models.usuario import Usuario


def registrar_salida(db: Session, codigo_qr: str, usuario_id: int, notas: str | None = None) -> Movimiento:
    material = db.query(Material).filter(Material.codigo_qr == codigo_qr).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if material.estado == "baja":
        raise HTTPException(status_code=400, detail="Este material está dado de baja")

    if material.estado == "prestado":
        # Buscar a quién está prestado
        ultimo = (
            db.query(Movimiento)
            .filter(Movimiento.material_id == material.id, Movimiento.tipo == "salida")
            .order_by(Movimiento.fecha_hora.desc())
            .first()
        )
        nombre = "alguien"
        if ultimo:
            u = db.query(Usuario).filter(Usuario.id == ultimo.usuario_id).first()
            if u:
                nombre = f"{u.nombre} {u.apellido}"
        raise HTTPException(status_code=409, detail=f"Ya está prestado a {nombre}")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.activo == True).first()  # noqa: E712
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    movimiento = Movimiento(
        material_id=material.id,
        usuario_id=usuario_id,
        tipo="salida",
        notas=notas,
    )
    db.add(movimiento)
    material.estado = "prestado"
    db.commit()
    db.refresh(movimiento)
    db.refresh(material)
    return movimiento


def registrar_entrada(db: Session, codigo_qr: str, notas: str | None = None) -> Movimiento:
    material = db.query(Material).filter(Material.codigo_qr == codigo_qr).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if material.estado != "prestado":
        raise HTTPException(status_code=409, detail="Este objeto no está prestado actualmente")

    ultimo_salida = (
        db.query(Movimiento)
        .filter(Movimiento.material_id == material.id, Movimiento.tipo == "salida")
        .order_by(Movimiento.fecha_hora.desc())
        .first()
    )
    if not ultimo_salida:
        raise HTTPException(status_code=500, detail="No se encontró el registro de salida")

    movimiento = Movimiento(
        material_id=material.id,
        usuario_id=ultimo_salida.usuario_id,
        tipo="entrada",
        notas=notas,
    )
    db.add(movimiento)
    material.estado = "disponible"
    db.commit()
    db.refresh(movimiento)
    db.refresh(material)
    return movimiento
