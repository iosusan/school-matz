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
    qr_base_url: str = "https://materiales.local"
    qr_images_dir: str = "./static/qr"
    secret_key: str = ""
    access_token_expire_hours: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def _ensure_secret_key(self) -> "Settings":
        if not self.secret_key:
            self.secret_key = _load_or_create_secret_key()
        return self


settings = Settings()
