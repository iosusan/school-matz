from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_admin
from backend.database import get_db
from backend.models.admin_user import AdminUser
from backend.models.categoria import Categoria
from backend.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    # Devuelve solo las categorías raíz; los hijos se incluyen en el schema anidado
    return db.query(Categoria).filter(Categoria.padre_id == None).all()  # noqa: E711


@router.get("/{categoria_id}", response_model=CategoriaOut)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.post("", response_model=CategoriaOut, status_code=201)
def crear_categoria(
    data: CategoriaCreate, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)
):
    if data.padre_id:
        padre = db.query(Categoria).filter(Categoria.id == data.padre_id).first()
        if not padre:
            raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
    cat = Categoria(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{categoria_id}", status_code=204)
def eliminar_categoria(
    categoria_id: int, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)
):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if cat.material:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: hay material en esta categoría",
        )
    db.delete(cat)
    db.commit()
