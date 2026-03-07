from datetime import datetime

from pydantic import BaseModel

from backend.schemas.categoria import CategoriaOut


class MaterialBase(BaseModel):
    descripcion: str
    categoria_id: int | None = None
    notas: str | None = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    descripcion: str | None = None
    categoria_id: int | None = None
    notas: str | None = None
    estado: str | None = None


class MaterialOut(MaterialBase):
    id: int
    codigo_qr: str
    estado: str
    created_at: datetime
    categoria: CategoriaOut | None = None

    model_config = {"from_attributes": True}
