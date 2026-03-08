from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_domain: str = "localhost"
    meta_admin_username: str = "admin"
    meta_admin_password_hash: str = ""
    meta_secret_key: str = "dev-insecure-key-change-in-production"
    access_token_expire_hours: int = 8

    # Ruta al directorio de tenants dentro del contenedor
    # (bind mount: host ./tenants → /app/tenants)
    tenants_dir: str = "/app/tenants"

    # Ruta a la plantilla Jinja2 del compose por tenant
    tenant_compose_template: str = "/app/docker/tenant-compose.yml.j2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
