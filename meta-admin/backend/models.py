from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

TenantEstado = Literal["creating", "running", "stopped", "error"]


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    base_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_username: Mapped[str] = mapped_column(String(64), nullable=False)
    estado: Mapped[str] = mapped_column(String(16), nullable=False, default="creating")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
