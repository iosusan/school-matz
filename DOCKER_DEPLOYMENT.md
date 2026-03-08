# DOCKER_DEPLOYMENT — Plan de Contenedorización y Despliegue

> **Versión:** 1.0
> **Fecha:** Marzo 2026
> **Aplicación:** school_matz — Sistema de Gestión de Material Escolar

---

## Índice

1. [Por qué Docker](#1-por-qué-docker)
2. [Arquitectura de contenedores](#2-arquitectura-de-contenedores)
3. [Dockerfile de la aplicación](#3-dockerfile-de-la-aplicación)
4. [Nginx adaptado para Docker](#4-nginx-adaptado-para-docker)
5. [docker-compose.yml](#5-docker-composeyml)
6. [Variables de entorno](#6-variables-de-entorno)
7. [Despliegue local (reemplazo del systemd actual)](#7-despliegue-local-reemplazo-del-systemd-actual)
8. [Multi-arquitectura — Raspberry Pi ARM](#8-multi-arquitectura--raspberry-pi-arm)
9. [Despliegue en AWS con Docker](#9-despliegue-en-aws-con-docker)
10. [Backups de datos](#10-backups-de-datos)
11. [Actualización de la aplicación](#11-actualización-de-la-aplicación)
12. [Seguridad](#12-seguridad)
13. [Referencia rápida de comandos](#13-referencia-rápida-de-comandos)

---

## 1. Por qué Docker

El sistema actual corre directamente sobre Ubuntu con Poetry + uvicorn + systemd + nginx instalados en el host. Docker aporta las siguientes ventajas:

| Ventaja | Descripción |
|---|---|
| **Portabilidad** | El mismo `docker-compose up` funciona en Ubuntu, Debian, Raspberry Pi OS, macOS, Windows y en cualquier cloud |
| **Aislamiento** | No contamina el sistema operativo del host con dependencias Python |
| **Reproducibilidad** | La imagen captura exactamente las mismas versiones de dependencias que funcionan en producción |
| **Despliegue en cloud trivial** | Subir la imagen a un registro y ejecutarla en EC2/Raspberry Pi/cualquier VPS |
| **Rollback instantáneo** | Si una actualización falla, volver a la imagen anterior es un solo comando |
| **Base de datos persistente** | SQLite en un volumen Docker nombrado — sobrevive a recreaciones del contenedor |

### Lo que NO cambia

- El código de la aplicación (FastAPI, modelos, routers, frontend) no necesita ningún cambio.
- La base de datos SQLite sigue siendo un único fichero. Solo cambia dónde vive (volumen Docker en lugar de `./data/`).
- Los certificados mkcert siguen funcionando del mismo modo — se montan en el contenedor Nginx.

---

## 2. Arquitectura de contenedores

El sistema se divide en dos servicios Docker:

```
┌──────────────────────────────────────────────────────────┐
│  Docker Compose — red interna: school_net                │
│                                                          │
│  ┌────────────────────┐    ┌──────────────────────────┐  │
│  │  nginx             │    │  app                     │  │
│  │  imagen: nginx:    │    │  imagen: school-assets   │  │
│  │  alpine            │    │  (build local)           │  │
│  │                    │    │                          │  │
│  │  Puerto 80  (HTTP) │───►│  Puerto 8000             │  │
│  │  Puerto 443 (HTTPS)│    │  uvicorn backend.main:app│  │
│  │                    │    │                          │  │
│  │  proxy_pass        │    │  Volúmenes:              │  │
│  │  → app:8000        │    │  - db_data:/app/data     │  │
│  └────────────────────┘    │  - qr_cache:/app/static  │  │
│         ▲                  └──────────────────────────┘  │
│         │                                                 │
│  Montajes del host:                                       │
│  ./certs/ → /certs/:ro                                    │
└──────────────────────────────────────────────────────────┘
         │
    Puertos expuestos al host:
    0.0.0.0:80  → nginx:80
    0.0.0.0:443 → nginx:443
```

### Volúmenes nombrados

| Volumen | Contenido | Por qué nombrado (no bind mount) |
|---|---|---|
| `db_data` | `data/assets.db` — base de datos SQLite | Gestionado por Docker, sobrevive a `down --volumes` si no se especifica `-v`; fácil de exportar para backup |
| `qr_cache` | `static/qr/` — imágenes QR del material | Se regeneran si se borran, pero conservarlos evita regeneración innecesaria |
| `qr_usuarios` | `static/qr_usuarios/` — QR de carnets de usuario | Ídem |

---

## 3. Dockerfile de la aplicación

Crear el fichero **`Dockerfile`** en la raíz del proyecto:

```dockerfile
# Dockerfile
# ─────────────────────────────────────────────────────────────
# Build: python:3.10-slim — imagen base ligera (~130 MB)
# Compatible con amd64 y arm64 (Raspberry Pi 4/5)
# ─────────────────────────────────────────────────────────────
FROM python:3.10-slim

# Instalar dependencias del sistema requeridas por:
#   - Pillow (libjpeg, zlib)
#   - reportlab (libfreetype)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar Poetry (misma versión que el proyecto usa)
RUN pip install --no-cache-dir poetry==2.3.2

# Copiar solo los ficheros de dependencias primero (cacheo eficiente de capas)
COPY pyproject.toml poetry.lock ./

# Instalar dependencias en el sistema Python (sin crear venv dentro del contenedor)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Copiar el código de la aplicación
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Crear directorios de datos que no van en código
# (los volúmenes Docker se montarán encima de estos directorios)
RUN mkdir -p data static/qr static/qr_usuarios

# Uvicorn escucha en 0.0.0.0 para que Docker pueda redirigir el tráfico
EXPOSE 8000

# El PYTHONPATH es necesario porque los módulos se importan como "backend.xxx"
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `.dockerignore`

Crear **`.dockerignore`** en la raíz del proyecto para reducir el contexto de build (~400 MB → ~5 MB):

```
.venv/
.git/
data/
certs/
__pycache__/
**/__pycache__/
*.pyc
*.pyo
.env
static/qr/*
static/qr_usuarios/*
```

---

## 4. Nginx adaptado para Docker

El fichero `scripts/nginx-materiales.conf` usa rutas absolutas del host y `127.0.0.1:8000`. Para Docker hay que adaptar dos cosas:

1. **Las rutas de certificados** cambian de `./certs/` del host a `/certs/` (punto de montaje del contenedor nginx).
2. **El backend** cambia de `127.0.0.1:8000` a `app:8000` (nombre del servicio en la red Docker).

La configuración nginx para Docker se gestiona como **plantilla + fichero generado**:

- **`docker/nginx.conf.template`** — fuente con el placeholder `__DOMAIN__` (versionado en git)
- **`docker/nginx.conf`** — generado por `bash docker/setup.sh`, montado en el contenedor (en `.gitignore`)

```
bash docker/setup.sh   →   sed 's/__DOMAIN__/materiales.local/g'   →   docker/nginx.conf
```

El contenido de la plantilla `docker/nginx.conf.template` — ver el fichero en el repositorio.

> **Nota:** `docker/nginx.conf` es generado automáticamente y está en `.gitignore`. No editar a mano.

---

## 5. docker-compose.yml

Crear **`docker-compose.yml`** en la raíz del proyecto:

```yaml
# docker-compose.yml
# ─────────────────────────────────────────────────────────────
# Dos servicios: app (FastAPI) y nginx (proxy inverso + SSL)
# Conexión entre ellos via red interna school_net.
# ─────────────────────────────────────────────────────────────

services:

  # ── Aplicación FastAPI ─────────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: school-assets-app
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      # Base de datos SQLite — persistente entre reinicios
      - db_data:/app/data
      # Caché de imágenes QR del material
      - qr_cache:/app/static/qr
      # Imágenes QR de carnets de usuario
      - qr_usuarios:/app/static/qr_usuarios
    networks:
      - school_net
    # App NO expone puertos al host directamente; solo nginx llega a ella
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/usuarios')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ── Nginx (proxy inverso + SSL) ────────────────────────────
  nginx:
    image: nginx:1.27-alpine
    container_name: school-assets-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      # Configuración específica para Docker (usa app:8000)
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      # Certificados mkcert montados en solo lectura
      - ./certs:/certs:ro
    depends_on:
      app:
        condition: service_healthy
    networks:
      - school_net

# ── Volúmenes nombrados ────────────────────────────────────
volumes:
  db_data:
    driver: local
  qr_cache:
    driver: local
  qr_usuarios:
    driver: local

# ── Red interna ────────────────────────────────────────────
networks:
  school_net:
    driver: bridge
```

### Estructura de ficheros resultante

```
school_matz/
├── Dockerfile              ← NUEVO
├── .dockerignore           ← NUEVO
├── docker-compose.yml      ← NUEVO
├── docker/
│   └── nginx.conf          ← NUEVO (adaptado de scripts/nginx-materiales.conf)
├── backend/
├── frontend/
├── certs/                  ← montado en nginx, no en la imagen
├── data/                   ← reemplazado por volumen Docker db_data
├── static/                 ← reemplazado por volúmenes Docker qr_cache / qr_usuarios
└── ...
```

---

## 6. Variables de entorno

El fichero `.env` actual es compatible con Docker sin cambios. Verificar que contiene:

```ini
# .env
DATABASE_URL=sqlite:///./data/assets.db
QR_BASE_URL=https://materiales.local
QR_IMAGES_DIR=./static/qr
```

> La ruta `./data/assets.db` es relativa al `WORKDIR=/app` del contenedor, donde el volumen `db_data` estará montado en `/app/data`. Todo funciona correctamente.

---

## 7. Despliegue local (reemplazo del systemd actual)

### Prerrequisitos

- Docker Engine ≥ 24 instalado: `sudo apt install docker.io docker-compose-v2`
- El usuario en el grupo `docker`: `sudo usermod -aG docker $USER && newgrp docker`

### Paso 0 (OBLIGATORIO): Configuración inicial

Antes del primer `docker compose up`, ejecuta el asistente de configuración:

```bash
cd /home/iosu/projects/school_matz

bash docker/setup.sh
```

El asistente hace de forma interactiva:
1. **Pregunta el dominio** bajo el que se servirá la aplicación (ej. `materiales.local`)
2. **Genera el certificado** SSL — si `mkcert` está instalado lo usa; si no, genera uno autofirmado
3. **Renderiza `docker/nginx.conf`** desde la plantilla `docker/nginx.conf.template`

```
  🐳 School Assets Docker — Configuración inicial

  Dominio [materiales.local]: assets.miescuela.local
  ✅ Dominio: assets.miescuela.local
  ✅ Certificado mkcert generado.
  ✅ docker/nginx.conf generado.

  Siguiente paso: docker compose up -d
```

Para cambiar el dominio en el futuro, vuelve a ejecutar `bash docker/setup.sh` y luego `docker compose up -d`.

### Primera vez: construir y arrancar

```bash
# 1. Construir la imagen (tarda ~2-3 min la primera vez)
docker compose build

# 2. Arrancar los dos contenedores en segundo plano
docker compose up -d

# 3. Verificar que ambos contenedores están corriendo
docker compose ps
```

Salida esperada:
```
NAME                    STATUS          PORTS
school-assets-app       running         8000/tcp
school-assets-nginx     running         0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Parar el sistema anterior (systemd) antes de arrancar Docker

Si el servicio systemd sigue activo, nginx de Docker no podrá usar los puertos 80 y 443:

```bash
# Parar y deshabilitar el servicio systemd de la app
sudo systemctl stop school-assets.service
sudo systemctl disable school-assets.service

# Parar nginx del host (Docker nginx tomará su lugar)
sudo systemctl stop nginx
sudo systemctl disable nginx
```

> **Nota:** se puede optar por dejar nginx del host corriendo y eliminarlo del docker-compose.yml, pasando la app al puerto 443 directamente. Sin embargo, la opción más limpia es mover también nginx a Docker.

### Verificar que todo funciona

```bash
# Comprobar logs de la app
docker compose logs app --tail 30

# Comprobar logs de nginx
docker compose logs nginx --tail 20

# Probar la API desde el servidor (usa el dominio configurado)
DOMAIN=$(cat config/domain)
curl -sk "https://${DOMAIN}/api/v1/usuarios" | python3 -m json.tool | head -10

# Descargar rootCA (prueba de HTTP y redirección)
curl -si "http://${DOMAIN}/rootCA.pem" | head -5
```

### Hacer que Docker se inicie con el sistema

El flag `restart: unless-stopped` en docker-compose.yml hace que los contenedores se reinicien solos después de un reboot, siempre que Docker Engine esté habilitado:

```bash
sudo systemctl enable docker
```

---

## 8. Multi-arquitectura — Raspberry Pi ARM

La imagen base `python:3.10-slim` soporta `linux/amd64` y `linux/arm64` (Raspberry Pi 4/5 con Ubuntu de 64 bits o Raspberry Pi OS de 64 bits).

### Construir en la propia Raspberry Pi

```bash
# En la Raspberry Pi, con Docker instalado
git clone <repositorio> /opt/school_matz
cd /opt/school_matz

# Build nativo — Docker detecta arm64 automáticamente
docker compose build
docker compose up -d
```

El build tarda más en Raspberry Pi (~5-8 min) pero el resultado es idéntico. No es necesario usar imágenes cruzadas ni emulación.

### Construir en amd64 para desplegar en arm64

Si se quiere construir la imagen en el portátil y transferirla a la Raspberry Pi:

```bash
# En el portátil (amd64) — requiere Docker Buildx habilitado
docker buildx build \
  --platform linux/arm64 \
  -t school-assets:latest \
  --output type=docker \
  .

# Exportar la imagen a un fichero
docker save school-assets:latest | gzip > school-assets-arm64.tar.gz

# Copiar a la Raspberry Pi
scp school-assets-arm64.tar.gz pi@192.168.1.X:/opt/

# En la Raspberry Pi: importar y arrancar
docker load < /opt/school-assets-arm64.tar.gz
docker compose up -d
```

### Nota sobre mDNS en Raspberry Pi

La resolución de `materiales.local` requiere Avahi en el host. Con Docker, Avahi sigue siendo del host, no del contenedor. Los pasos son los mismos que en el despliegue sin Docker:

```bash
sudo bash scripts/setup_avahi.sh
```

---

## 9. Despliegue en AWS con Docker

Docker simplifica enormemente el despliegue en la nube: se construye la imagen una vez y se ejecuta en cualquier instancia EC2 con Docker instalado.

### 9.1 Preparar la instancia EC2

```bash
# Conectar a la instancia
ssh -i mi-clave.pem ubuntu@<IP_PUBLICA>

# Instalar Docker y Compose
sudo apt update && sudo apt install -y docker.io
sudo usermod -aG docker ubuntu
newgrp docker

# Comprobar versión
docker --version
docker compose version
```

### 9.2 Opción A: Clonar el repositorio directamente

```bash
# Clonar el proyecto en la instancia
git clone <repositorio> /opt/school_matz
cd /opt/school_matz

# Configurar .env para producción
cp .env.example .env
nano .env
```

Contenido del `.env` para producción en AWS:
```ini
DATABASE_URL=sqlite:///./data/assets.db
QR_BASE_URL=https://mi-dominio.com
QR_IMAGES_DIR=./static/qr
```

```bash
# Construir y arrancar (sin nginx de Docker: usar el del host con certbot)
docker compose up -d app
```

### 9.3 SSL en AWS con Let's Encrypt (sin contenedor nginx)

En cloud, el certificado SSL viene de Let's Encrypt en lugar de mkcert. La forma más sencilla es usar nginx del host como proxy:

```bash
# Installar nginx y certbot en el host EC2
sudo apt install -y nginx certbot python3-certbot-nginx

# Configurar nginx como proxy hacia el contenedor de la app
sudo nano /etc/nginx/sites-available/school-assets
```

```nginx
# /etc/nginx/sites-available/school-assets (en el HOST de EC2)
server {
    server_name mi-dominio.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/school-assets /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Obtener certificado SSL gratuito
sudo certbot --nginx -d mi-dominio.com
```

En este caso, el docker-compose.yml en AWS necesita exponer el puerto 8000 al host:

```yaml
# Modificación para AWS (sin nginx en Docker)
services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"   # Solo accesible desde el host, no desde internet
    volumes:
      - db_data:/app/data
      - qr_cache:/app/static/qr
      - qr_usuarios:/app/static/qr_usuarios
    env_file:
      - .env
```

### 9.4 Opción B: Imagen en Docker Hub o ECR

Para un despliegue más profesional, separar el build del despliegue:

```bash
# En el portátil: construir y publicar en Docker Hub
docker build -t tuusuario/school-assets:1.0 .
docker push tuusuario/school-assets:1.0

# ──────────────────────────────────────────────────────
# En la instancia EC2:
docker pull tuusuario/school-assets:1.0
docker run -d \
  --name school-assets-app \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -v /opt/school-assets/data:/app/data \
  -v /opt/school-assets/static/qr:/app/static/qr \
  -v /opt/school-assets/static/qr_usuarios:/app/static/qr_usuarios \
  --env-file /opt/school-assets/.env \
  tuusuario/school-assets:1.0
```

---

## 10. Backups de datos

### Qué hay que preservar

| Dato | Localización en Docker | Criticidad |
|---|---|---|
| Base de datos SQLite | Volumen `db_data` → `/var/lib/docker/volumes/school_matz_db_data/` | ⚠️ CRÍTICO |
| Imágenes QR de material | Volumen `qr_cache` | Media — se regeneran automáticamente |
| Imágenes QR de usuarios | Volumen `qr_usuarios` | Media — se regeneran automáticamente |
| Certificados mkcert | `./certs/` (bind mount, en el repositorio) | Baja — regenerables con `setup_mkcert.sh` |

### Backup de la base de datos

```bash
# Backup manual — copia el fichero desde el volumen
docker compose exec app cp /app/data/assets.db /app/data/assets_$(date +%Y%m%d_%H%M).db

# O directamente desde el host, accediendo al directorio del volumen
sudo cp /var/lib/docker/volumes/school_matz_db_data/_data/assets.db \
  /home/iosu/backups/assets_$(date +%Y%m%d_%H%M).db
```

### Backup automático con cron

```bash
# Abrir crontab
crontab -e

# Añadir — backup diario a las 22:00, conservar los últimos 30 días
0 22 * * * docker exec school-assets-app cp /app/data/assets.db /app/data/assets_$(date +\%Y\%m\%d).db && find /var/lib/docker/volumes/school_matz_db_data/_data/ -name "assets_*.db" -mtime +30 -delete
```

### Restaurar desde backup

```bash
# Parar la app para evitar escrituras concurrentes
docker compose stop app

# Copiar el backup al volumen
sudo cp /home/iosu/backups/assets_20260307.db \
  /var/lib/docker/volumes/school_matz_db_data/_data/assets.db

# Reiniciar
docker compose start app
```

---

## 11. Actualización de la aplicación

### Proceso de actualización

```bash
cd /home/iosu/projects/school_matz

# 1. Obtener cambios del repositorio
git pull

# 2. Reconstruir la imagen con los nuevos cambios
docker compose build app

# 3. Reiniciar solo el contenedor de la app (nginx sigue en pie)
docker compose up -d --no-deps app

# 4. Verificar que arrancó correctamente
docker compose logs app --tail 20
docker compose ps
```

> Los volúmenes `db_data`, `qr_cache` y `qr_usuarios` no se tocan en el proceso de actualización — los datos persisten intactos.

### Rollback a la versión anterior

```bash
# Ver el historial de imágenes construidas
docker images school_matz-app

# Etiquetar la imagen actual antes de actualizar (precaución)
docker tag school_matz-app:latest school_matz-app:backup-$(date +%Y%m%d)

# Si la actualización falla, restaurar la imagen anterior
docker compose down app
docker tag school_matz-app:backup-20260307 school_matz-app:latest
docker compose up -d app
```

---

## 12. Seguridad

### Reducción de superficie de ataque

- La app **no expone el puerto 8000 al exterior** — nginx es el único punto de entrada.
- El contenedor `app` corre con el usuario no privilegiado de Python (`root` en la imagen base slim — mejorable añadiendo `USER app` al Dockerfile).
- Los certificados se montan como **solo lectura** (`./certs:/certs:ro`).
- La configuración de nginx tiene solo los protocolos TLS modernos (`TLSv1.2 TLSv1.3`).

### Añadir un usuario no-root al Dockerfile

Para mayor seguridad, añadir al Dockerfile antes del CMD:

```dockerfile
# Crear usuario no-root para ejecutar la app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser
```

### Limitación de recursos del contenedor

Si el servidor es compartido, limitar CPU y memoria para que la app no monopolice el sistema:

```yaml
# Añadir en docker-compose.yml bajo el servicio app:
services:
  app:
    ...
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
        reservations:
          memory: 128M
```

### Despliegue en cloud — consideraciones de seguridad adicionales

En cloud, el sistema es accesible desde internet. Ver la sección 15.7 de `SCHOOL_ASSET_MGMT.md` para una lista completa. Lo mínimo imprescindible:

```bash
# Fail2ban para bloquear escaneos automáticos
sudo apt install fail2ban

# Actualizaciones de seguridad automáticas
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 13. Referencia rápida de comandos

```bash
# ── Ciclo de vida ─────────────────────────────────────────
# Construir imágenes
docker compose build

# Arrancar en segundo plano
docker compose up -d

# Parar y eliminar contenedores (los volúmenes se conservan)
docker compose down

# Parar y eliminar contenedores Y volúmenes (¡borra la DB!)
docker compose down -v

# ── Logs ─────────────────────────────────────────────────
docker compose logs -f            # Todos los servicios, en tiempo real
docker compose logs app --tail 50 # Últimas 50 líneas de la app
docker compose logs nginx         # Logs de nginx

# ── Estado ───────────────────────────────────────────────
docker compose ps                 # Estado de los contenedores
docker stats                      # Uso de CPU y RAM en tiempo real

# ── Depuración ───────────────────────────────────────────
docker compose exec app bash      # Shell dentro del contenedor de la app
docker compose exec nginx sh      # Shell en el contenedor nginx (Alpine → sh)

# ── Base de datos ─────────────────────────────────────────
# Acceso interactivo a la SQLite dentro del contenedor
docker compose exec app python3 -c "
import sqlite3
con = sqlite3.connect('/app/data/assets.db')
cur = con.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print(cur.fetchall())
"

# ── Imágenes ─────────────────────────────────────────────
docker images                     # Ver imágenes construidas
docker image prune                # Eliminar imágenes sin usar (libera espacio)

# ── Build limpio (sin caché) ──────────────────────────────
docker compose build --no-cache
```

---

## Apéndice A — Árbol de ficheros Docker que hay que crear

```
school_matz/
├── Dockerfile              ← Build de la imagen de la app
├── .dockerignore           ← Excluir .venv, data, certs, static del contexto
├── docker-compose.yml      ← Orquestación app + nginx
└── docker/
    └── nginx.conf          ← Config nginx adaptada para Docker (app:8000, /certs/)
```

## 14. Despliegue Multitenant (Traefik + Meta-admin)

Para gestionar múltiples centros escolares en el mismo servidor, consulta
[MULTI_TENANT.md](MULTI_TENANT.md). A continuación, un resumen de las diferencias
respecto al despliegue sencillo de esta guía:

| Aspecto | Despliegue simple | Despliegue multitenant |
|---|---|---|
| Reverse proxy | Nginx (en Docker o en host) | **Traefik v3.6** |
| TLS | mkcert (local) / certbot (cloud) | **Let's Encrypt automático** |
| Stack principal | `docker-compose.yml` | `docker-compose.infra.yml` |
| Imagen de la app | construida en `docker-compose.yml` | `school-matz:latest` (preconstruida) |
| Gestión de tenants | manual | **Meta-admin** en `meta.{dominio}` |

### Primer despliegue multitenant

```bash
# Prerrequisito: DNS *.miescuela.es → IP del servidor

# 1. Inicializar infraestructura base (una sola vez)
bash scripts/init-infra.sh

# 2. Editar traefik/traefik.yml → poner email real en acme.email

# 3. Configurar meta-admin
cp meta-admin/.env.example meta-admin/.env
# Establecer BASE_DOMAIN, META_ADMIN_USERNAME y META_ADMIN_PASSWORD_HASH
# Generar hash: python3 -c "import bcrypt; print(bcrypt.hashpw(b'tu-password', bcrypt.gensalt()).decode())"

# 4. Construir imagen base de la app
bash scripts/build-app-image.sh

# 5. Levantar el stack de infraestructura
docker compose -f docker-compose.infra.yml up -d

# 6. Verificar
docker compose -f docker-compose.infra.yml ps
curl -s https://meta.miescuela.es/api/v1/auth/login \
  -X POST -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"tu-password"}'
```

### Actualizar la app para todos los tenants

```bash
# Reconstruir imagen con el nuevo código
bash scripts/build-app-image.sh

# Recrear el contenedor de un tenant concreto (cero downtime si hay replicación)
docker compose -f tenants/<slug>/docker-compose.yml up -d --force-recreate
```

### Backup multitenant

```bash
# Backup de todos los tenants
for slug in tenants/*/; do
  slug=$(basename "$slug")
  cp tenants/${slug}/data/assets.db backups/${slug}-$(date +%Y%m%d).db
done

# Backup de la base de datos del meta-admin
cp meta-admin/data/meta.db backups/meta-$(date +%Y%m%d).db
```

---

## Apéndice B — Verificación completa post-despliegue

```bash
# 1. Ambos contenedores en estado running
docker compose ps

# 2. API responde
curl -sk https://materiales.local/api/v1/usuarios | python3 -m json.tool | head -5

# 3. HTTP redirige a HTTPS
curl -si http://materiales.local/ | grep -i "location"
# Esperado: Location: https://materiales.local/

# 4. rootCA descargable por HTTP
curl -si http://materiales.local/rootCA.pem | head -3
# Esperado: HTTP/1.1 200 OK

# 5. PDF de carnets genera correctamente (theme EducaMadrid)
curl -sk -o /tmp/test.pdf -w "%{http_code}" \
  "https://materiales.local/api/v1/usuarios/pdf-carnets?theme=educamadrid"
# Esperado: 200

# 6. PDF de carnets tema CEIP
curl -sk -o /tmp/test_ceip.pdf -w "%{http_code}" \
  "https://materiales.local/api/v1/usuarios/pdf-carnets?theme=ceip"
# Esperado: 200
```
