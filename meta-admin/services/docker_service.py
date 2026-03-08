import secrets
import shutil
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from backend.config import settings


class DockerService:
    """Gestión del ciclo de vida de contenedores de tenants via docker compose."""

    def __init__(self) -> None:
        self._tenants_dir = Path(settings.tenants_dir)
        template_path = Path(settings.tenant_compose_template)
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=False,
        )
        self._template_name = template_path.name

    # ── Ciclo de vida ─────────────────────────────────────────

    def deploy(
        self,
        slug: str,
        base_domain: str,
        admin_username: str,
        admin_password: str,
    ) -> None:
        """Crea el directorio del tenant, genera su compose y lo levanta."""
        tenant_dir = self._tenant_dir(slug)
        self._prepare_dirs(tenant_dir)

        secret_key = secrets.token_hex(32)
        compose_content = self._render_compose(slug, base_domain, secret_key)
        (tenant_dir / "docker-compose.yml").write_text(compose_content)

        self._compose_run(slug, ["up", "-d", "--wait"])
        self._create_superadmin(slug, admin_username, admin_password)

    def start(self, slug: str) -> None:
        self._compose_run(slug, ["start"])

    def stop(self, slug: str) -> None:
        self._compose_run(slug, ["stop"])

    def destroy(self, slug: str) -> None:
        """Para y elimina los contenedores del tenant y borra todos sus datos (BD, QR, compose)."""
        tenant_dir = self._tenant_dir(slug)
        if tenant_dir.exists():
            self._compose_run(slug, ["down", "--remove-orphans"])
            shutil.rmtree(tenant_dir)

    # ── Helpers internos ──────────────────────────────────────

    def _tenant_dir(self, slug: str) -> Path:
        return self._tenants_dir / slug

    def _prepare_dirs(self, tenant_dir: Path) -> None:
        (tenant_dir / "data").mkdir(parents=True, exist_ok=True)
        (tenant_dir / "static" / "qr").mkdir(parents=True, exist_ok=True)
        (tenant_dir / "static" / "qr_usuarios").mkdir(parents=True, exist_ok=True)

    def _render_compose(self, slug: str, base_domain: str, secret_key: str) -> str:
        template = self._jinja_env.get_template(self._template_name)
        return template.render(
            tenant_slug=slug,
            base_domain=base_domain,
            secret_key=secret_key,
        )

    def _compose_run(self, slug: str, args: list[str]) -> None:
        compose_file = self._tenant_dir(slug) / "docker-compose.yml"
        if not compose_file.exists():
            raise FileNotFoundError(f"No se encontró compose para el tenant '{slug}'")
        cmd = ["docker", "compose", "-f", str(compose_file)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"docker compose {' '.join(args)} falló")

    def _create_superadmin(self, slug: str, username: str, password: str) -> None:
        """Ejecuta el script de creación de superadmin dentro del contenedor del tenant."""
        container = f"tenant-{slug}"
        # Las credenciales se pasan como variables de entorno para evitar
        # problemas de escape y no exponerlas en la línea de comandos.
        script = (
            "import sys, os; sys.path.insert(0,'.');"
            "from backend.database import Base, engine;"
            "from backend.models.admin_user import AdminUser;"
            "from backend.auth import hash_password;"
            "from sqlalchemy.orm import Session;"
            "Base.metadata.create_all(bind=engine);"
            "u=AdminUser("
            "username=os.environ['_ADMIN_USER'],"
            "password_hash=hash_password(os.environ['_ADMIN_PASS']),"
            "is_superadmin=True);"
            "db=Session(engine); db.add(u); db.commit(); db.close();"
            "print('superadmin creado')"
        )
        cmd = [
            "docker",
            "exec",
            "-e",
            f"_ADMIN_USER={username}",
            "-e",
            f"_ADMIN_PASS={password}",
            container,
            "python",
            "-c",
            script,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Error creando superadmin en tenant '{slug}': {result.stderr.strip()}"
            )
