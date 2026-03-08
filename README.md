
# 🏫 School Assets — Sistema de Gestión de Material Escolar

Aplicación web para gestionar préstamos de material en un aula escolar.
Frontend SPA en Vanilla JS + Tailwind CSS; backend FastAPI + SQLite.

---

## Características

- Registro y préstamo de material con códigos QR
- Carnets de usuario con QR imprimibles en PDF
- Panel de administración protegido con login (JWT)
- Superadministrador configurado en el primer arranque
- Dominio local configurable (`materiales.local` por defecto)
- Certificado HTTPS con mkcert (sin advertencias en el navegador)
- Soporte para despliegue local (systemd + nginx) y Docker

---

## Inicio rápido — Modo local (sin Docker)

### 1. Configuración inicial (dominio, certificado, nginx y superadmin)

```bash
sudo bash scripts/first_run.sh
```

Este asistente interactivo:
1. Pregunta el dominio (por defecto `materiales.local`) y lo guarda en `config/domain`
2. Genera el certificado HTTPS con mkcert (o autofirmado si no está instalado)
3. Configura nginx como proxy inverso
4. Crea el superadministrador del panel de administración

### 2. Instalar el servicio systemd

```bash
sudo cp scripts/school-assets.service /etc/systemd/system/
sudo systemctl enable --now school-assets
```

### 3. Arrancar manualmente (desarrollo)

```bash
./start.sh
```

---

## Inicio rápido — Docker

### 1. Configuración inicial

```bash
bash docker/setup.sh
```

Genera `docker/nginx.conf`, los certificados en `./certs/` y la `SECRET_KEY` en `.env`.

### 2. Levantar los contenedores

```bash
docker compose up --build -d
```

### 3. Crear el superadministrador (primera vez)

```bash
docker exec -it school-assets-app bash scripts/prepare_root.sh
```

O de forma no interactiva:

```bash
docker exec -e ADMIN_USER=admin -e ADMIN_PASS=<contraseña> \
  school-assets-app python scripts/create_superadmin.py
```

Para más detalles sobre el despliegue Docker, consulta [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

---

## Panel de administración

Accede desde la app principal pulsando **⚙️ Administración**, o directamente en `/admin.html`.

El panel está **protegido por login**. Solo el superadministrador puede acceder.
Las credenciales se configuran en el paso de `first_run.sh` / `prepare_root.sh`.

- El token de sesión se guarda en `sessionStorage` y expira en **8 horas**.
- Para cerrar sesión, pulsa el botón **Salir** en la cabecera del panel.
- Si el token expira, el formulario de login aparece automáticamente.

Para cambiar la contraseña o crear un nuevo superadmin en cualquier momento:

```bash
# Modo local
bash scripts/prepare_root.sh

# Docker
docker exec -it school-assets-app bash scripts/prepare_root.sh
```

---

## Instalar el certificado raíz en los dispositivos

Para que los navegadores no muestren advertencias de seguridad, instala el
certificado raíz **una sola vez** en cada dispositivo.

Descarga directa desde cualquier dispositivo en la misma WiFi:
```
http://materiales.local/rootCA.pem
```

### iOS / iPadOS
1. Abre `http://materiales.local/rootCA.pem` en **Safari** (se descarga automáticamente)
2. **Ajustes → General → VPN y gestión del dispositivo → Instalar perfil**
3. **Ajustes → General → Información → Confianza de certificados** →
   activa `mkcert root@...` como certificado raíz de confianza completa

### Android
> ⚠️ Chrome en Android 7+ no confía en CAs de usuario. Usa **Firefox para Android**.

1. Descarga `http://materiales.local/rootCA.pem`
2. **Ajustes → Seguridad → Credenciales de confianza → Instalar CA**
3. Firefox → `about:config` → `security.enterprise_roots.enabled` → `true`

### Windows / macOS
```bash
CAROOT=/home/iosu/projects/school_matz/certs/ca mkcert -install
```
O doble clic sobre `rootCA.pem` e instalar en «Entidades de certificación raíz de confianza».

---

## Variables de entorno (`.env`)

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/assets.db` | Ruta a la base de datos SQLite |
| `QR_BASE_URL` | `https://materiales.local` | URL base para los QR generados |
| `QR_IMAGES_DIR` | `./static/qr` | Directorio de imágenes QR del material |
| `SECRET_KEY` | *(auto-generada)* | Clave secreta para firma JWT. En modo local se genera en `config/secret_key`; en Docker debe estar en `.env` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `8` | Duración del token de sesión admin |

---

## Estructura de archivos relevante

```
backend/
  auth.py                  # Hashing bcrypt, JWT, dependencia get_current_admin
  models/admin_user.py     # Modelo AdminUser (tabla admin_users)
  routers/auth.py          # POST /api/v1/auth/login  GET /auth/me  GET /auth/status
config/
  domain                   # Dominio configurado (git-ignored)
  secret_key               # Clave JWT en modo local (git-ignored)
scripts/
  first_run.sh             # Setup interactivo completo (local)
  prepare_root.sh          # Crea/actualiza el superadmin (interactivo)
  create_superadmin.py     # Helper Python (lee ADMIN_USER + ADMIN_PASS por env)
docker/
  setup.sh                 # Setup interactivo para Docker
  nginx.conf.template      # Plantilla nginx con __DOMAIN__
```

---

## Desarrollo

```bash
# Instalar dependencias
poetry install

# Linter
poetry run ruff check backend/

# Arrancar servidor de desarrollo
./start.sh
```

Consulta [README_DEV.md](README_DEV.md) para detalles sobre herramientas de desarrollo,
convenciones de commits y generación de releases.
