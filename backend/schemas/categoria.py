from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CategoriaBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    padre_id: int | None = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    padre_id: int | None = None


class CategoriaOut(CategoriaBase):
    id: int
    created_at: datetime
    hijos: list[CategoriaOut] = []

    model_config = {"from_attributes": True}


CategoriaOut.model_rebuild()
