import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.auth import get_current_admin, hash_password
from backend.database import get_db
from backend.models.admin_user import AdminUser
from backend.models.usuario import Usuario
from backend.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from backend.services import pdf_carnet_service, qr_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


# ------ Rutas estáticas/prefijadas ANTES de las parametrizadas ------


@router.get("/pdf-carnets")
def descargar_pdf_carnets(
    ids: str | None = None, theme: str = "educamadrid", db: Session = Depends(get_db)
):
    """PDF con carnets. ids = lista separada por comas; omitir = todos los activos. theme = educamadrid|ceip."""
    q = db.query(Usuario).filter(Usuario.activo == True)  # noqa: E712
    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        q = q.filter(Usuario.id.in_(id_list))
    usuarios = q.order_by(Usuario.apellido, Usuario.nombre).all()
    if not usuarios:
        raise HTTPException(status_code=404, detail="No hay usuarios")

    pdf_bytes = pdf_carnet_service.generate_pdf_carnets(usuarios, theme=theme)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=carnets.pdf"},
    )


# ------ Rutas parametrizadas ------


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(solo_activos: bool = True, db: Session = Depends(get_db)):
    q = db.query(Usuario)
    if solo_activos:
        q = q.filter(Usuario.activo == True)  # noqa: E712
    return q.order_by(Usuario.apellido, Usuario.nombre).all()


@router.get("/{usuario_id}/qr/imagen")
def obtener_qr_imagen_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.codigo_qr:
        raise HTTPException(status_code=404, detail="Usuario o QR no encontrado")
    path = os.path.join("./static/qr_usuarios", f"usuario_{usuario_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Imagen QR no encontrada")
    return FileResponse(path, media_type="image/png")


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    data: UsuarioCreate, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)
):
    usuario = Usuario(**data.model_dump())
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    uuid4_token = str(uuid.uuid4())
    usuario.codigo_qr = hash_password(uuid4_token)
    db.commit()
    db.refresh(usuario)
    qr_service.generate_qr_usuario(usuario.id, uuid4_token, usuario.nombre, usuario.apellido)
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    fields_updated = data.model_dump(exclude_unset=True)
    for field, value in fields_updated.items():
        setattr(usuario, field, value)
    db.commit()
    db.refresh(usuario)
    if "nombre" in fields_updated or "apellido" in fields_updated:
        # Regenerar QR con nuevo nombre implica invalidar el carnet anterior
        uuid4_token = str(uuid.uuid4())
        usuario.codigo_qr = hash_password(uuid4_token)
        db.commit()
        db.refresh(usuario)
        qr_service.generate_qr_usuario(usuario.id, uuid4_token, usuario.nombre, usuario.apellido)
    return usuario


@router.post("/{usuario_id}/reset-qr")
def reset_qr_usuario(
    usuario_id: int,
    theme: str = "educamadrid",
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    """Genera un nuevo QR para el usuario (invalida el anterior) y devuelve el PDF del carnet."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    uuid4_token = str(uuid.uuid4())
    usuario.codigo_qr = hash_password(uuid4_token)
    db.commit()
    db.refresh(usuario)
    qr_service.generate_qr_usuario(usuario.id, uuid4_token, usuario.nombre, usuario.apellido)
    pdf_bytes = pdf_carnet_service.generate_pdf_carnets([usuario], theme=theme)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=carnet_{usuario_id}.pdf"},
    )


@router.delete("/{usuario_id}", status_code=204)
def desactivar_usuario(
    usuario_id: int, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = False
    db.commit()
