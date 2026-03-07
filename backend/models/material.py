from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Material(Base):
    __tablename__ = "material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_qr: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    categoria_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[str] = mapped_column(String, default="disponible")
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    categoria: Mapped["Categoria | None"] = relationship(  # noqa: F821
        "Categoria", back_populates="material"
    )
    movimientos: Mapped[list["Movimiento"]] = relationship(  # noqa: F821
        "Movimiento", back_populates="material"
    )
