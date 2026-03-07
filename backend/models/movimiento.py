from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Movimiento(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material.id"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)  # 'salida' | 'entrada'
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    material: Mapped["Material"] = relationship(  # noqa: F821
        "Material", back_populates="movimientos"
    )
    usuario: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario", back_populates="movimientos"
    )
