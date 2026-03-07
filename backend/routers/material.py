import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.material import Material
from backend.schemas.material import MaterialCreate, MaterialOut, MaterialUpdate
from backend.services.pdf_service import generar_pdf_etiquetas
from backend.services.qr_service import generate_qr_image

router = APIRouter(prefix="/material", tags=["material"])


def _next_codigo(db: Session) -> str:
    count = db.query(Material).count()
    return f"MAT-{(count + 1):05d}"


@router.get("", response_model=list[MaterialOut])
def listar_material(
    estado: str | None = None,
    categoria_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Material)
    if estado:
        query = query.filter(Material.estado == estado)
    if categoria_id:
        query = query.filter(Material.categoria_id == categoria_id)
    if q:
        query = query.filter(Material.descripcion.ilike(f"%{q}%"))
    return query.order_by(Material.descripcion).all()


@router.get("/qr/{codigo_qr}", response_model=MaterialOut)
def buscar_por_qr(codigo_qr: str, db: Session = Depends(get_db)):
    mat = db.query(Material).filter(Material.codigo_qr == codigo_qr).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return mat


@router.get("/pdf-etiquetas")
def pdf_etiquetas(
    estado: str | None = None,
    categoria_id: int | None = None,
    ids: str | None = None,      # lista separada por comas: "1,2,3"
    db: Session = Depends(get_db),
):
    """Devuelve un PDF con etiquetas QR listas para imprimir."""
    query = db.query(Material).filter(Material.estado != "baja")
    if estado:
        query = query.filter(Material.estado == estado)
    if categoria_id:
        query = query.filter(Material.categoria_id == categoria_id)
    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Material.id.in_(id_list))
    materiales = query.order_by(Material.descripcion).all()
    if not materiales:
        raise HTTPException(status_code=404, detail="No hay material que coincida con los filtros")
    pdf_bytes = generar_pdf_etiquetas(materiales)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=etiquetas_qr.pdf"},
    )


@router.get("/{material_id}", response_model=MaterialOut)
def obtener_material(material_id: int, db: Session = Depends(get_db)):
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return mat


@router.post("", response_model=MaterialOut, status_code=201)
def crear_material(data: MaterialCreate, db: Session = Depends(get_db)):
    codigo_qr = _next_codigo(db)
    mat = Material(codigo_qr=codigo_qr, **data.model_dump())
    db.add(mat)
    db.commit()
    db.refresh(mat)

    # Generar imagen QR
    cat_nombre = mat.categoria.nombre if mat.categoria else None
    generate_qr_image(codigo_qr, mat.descripcion, cat_nombre)

    return mat


@router.put("/{material_id}", response_model=MaterialOut)
def actualizar_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mat, field, value)
    db.commit()
    db.refresh(mat)
    return mat


@router.delete("/{material_id}", status_code=204)
def dar_de_baja(material_id: int, db: Session = Depends(get_db)):
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    mat.estado = "baja"
    db.commit()


@router.get("/{material_id}/qr/imagen")
def descargar_qr(material_id: int, db: Session = Depends(get_db)):
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    filepath = os.path.join(settings.qr_images_dir, f"{mat.codigo_qr}.png")
    if not Path(filepath).exists():
        cat_nombre = mat.categoria.nombre if mat.categoria else None
        generate_qr_image(mat.codigo_qr, mat.descripcion, cat_nombre)

    return FileResponse(filepath, media_type="image/png", filename=f"{mat.codigo_qr}.png")
