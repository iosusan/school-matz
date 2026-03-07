from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    padre_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    padre: Mapped["Categoria | None"] = relationship(
        "Categoria", remote_side="Categoria.id", back_populates="hijos"
    )
    hijos: Mapped[list["Categoria"]] = relationship(
        "Categoria", back_populates="padre", cascade="all, delete-orphan"
    )
    material: Mapped[list["Material"]] = relationship(  # noqa: F821
        "Material", back_populates="categoria"
    )
