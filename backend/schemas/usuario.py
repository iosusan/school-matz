from datetime import datetime

from pydantic import BaseModel


class UsuarioBase(BaseModel):
    nombre: str
    apellido: str


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    activo: bool | None = None


class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    codigo_qr: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
