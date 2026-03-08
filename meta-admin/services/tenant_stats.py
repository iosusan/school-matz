import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from backend.config import settings


class TenantStats:
    """Lee métricas directamente de la SQLite de un tenant."""

    def __init__(self, slug: str) -> None:
        db_path = Path(settings.tenants_dir) / slug / "data" / "assets.db"
        if not db_path.exists():
            raise FileNotFoundError(f"Base de datos del tenant '{slug}' no encontrada")
        self._db_path = db_path

    def get(self) -> dict:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            return {
                "usuarios_activos": self._count_usuarios(conn),
                "items_material": self._count_material(conn),
                "movimientos_30d": self._count_movimientos_30d(conn),
                "ultimo_movimiento": self._ultimo_movimiento(conn),
            }

    # ── Queries ───────────────────────────────────────────────

    def _count_usuarios(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1").fetchone()
        return row[0] if row else 0

    def _count_material(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT COUNT(*) FROM material WHERE activo = 1").fetchone()
        return row[0] if row else 0

    def _count_movimientos_30d(self, conn: sqlite3.Connection) -> int:
        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        row = conn.execute("SELECT COUNT(*) FROM movimientos WHERE fecha >= ?", (since,)).fetchone()
        return row[0] if row else 0

    def _ultimo_movimiento(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT MAX(fecha) FROM movimientos").fetchone()
        return row[0] if row and row[0] else None
