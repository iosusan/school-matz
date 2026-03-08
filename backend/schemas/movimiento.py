from datetime import datetime

from pydantic import BaseModel

from backend.schemas.material import MaterialOut
from backend.schemas.usuario import UsuarioOut


class SalidaRequest(BaseModel):
    codigo_qr: str
    notas: str | None = None


class EntradaRequest(BaseModel):
    codigo_qr: str
    notas: str | None = None


class MovimientoOut(BaseModel):
    id: int
    tipo: str
    fecha_hora: datetime
    notas: str | None = None
    material: MaterialOut
    usuario: UsuarioOut

    model_config = {"from_attributes": True}


class SalidaResponse(BaseModel):
    ok: bool
    movimiento_id: int
    material: MaterialOut
    usuario: UsuarioOut
    fecha_hora: datetime


class EntradaResponse(BaseModel):
    ok: bool
    movimiento_id: int
    material: MaterialOut
    usuario: UsuarioOut
    fecha_hora: datetime


class PrestamoActivo(BaseModel):
    material: MaterialOut
    usuario: UsuarioOut
    desde: datetime
