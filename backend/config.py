import secrets
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_or_create_secret_key() -> str:
    key_file = Path("config/secret_key")
    if key_file.exists():
        val = key_file.read_text().strip()
        if val:
            return val
    key = secrets.token_hex(32)
    key_file.parent.mkdir(exist_ok=True)
    key_file.write_text(key + "\n")
    return key


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/assets.db"
    qr_base_url: str = ""
    qr_images_dir: str = "./static/qr"
    secret_key: str = ""
    access_token_expire_hours: int = 8

    # Multitenant: si se definen estas dos variables, qr_base_url se construye
    # automáticamente como https://{tenant_slug}.{base_domain}
    tenant_slug: str = ""
    base_domain: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def _ensure_defaults(self) -> "Settings":
        # Construir qr_base_url desde tenant_slug + base_domain si no está explícito
        if not self.qr_base_url:
            if self.tenant_slug and self.base_domain:
                self.qr_base_url = f"https://{self.tenant_slug}.{self.base_domain}"
            else:
                self.qr_base_url = "https://materiales.local"
        if not self.secret_key:
            self.secret_key = _load_or_create_secret_key()
        return self


settings = Settings()
