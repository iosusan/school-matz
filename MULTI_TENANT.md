# MULTI_TENANT — Plan de soporte multitenant

> **Versión:** 1.0
> **Fecha:** Marzo 2026
> **Estado:** Fase 1 ✅ · Fase 2 ✅ · Fase 3 ✅ · Fase 4 ✅ · Fase 5 ✅

---

## Índice

1. [Decisiones de diseño](#1-decisiones-de-diseño)
2. [Arquitectura objetivo](#2-arquitectura-objetivo)
3. [Estructura de ficheros](#3-estructura-de-ficheros)
4. [Componentes clave](#4-componentes-clave)
5. [Fases de implementación](#5-fases-de-implementación)
6. [Procedimientos operacionales](#6-procedimientos-operacionales)

---

## 1. Decisiones de diseño

| Parámetro | Decisión |
|---|---|
| Entorno de despliegue | Servidor único, Docker Compose |
| Enrutamiento | Subdominios: `{slug}.{base_domain}` |
| TLS | Let's Encrypt automático (ACME httpChallenge) |
| Reverse proxy | Traefik v3.6+ |
| Despliegue de tenants | `docker-compose.yml` generado desde plantilla Jinja2 + `docker compose up` |
| Meta-admin backend | FastAPI + Python |
| Meta-admin frontend | HTML + JavaScript estático |
| URL meta-admin | `meta.{base_domain}` |
| DB meta-admin | SQLite |
| DB por tenant | SQLite (fichero en bind mount del tenant) |
| Auth meta-admin | Único administrador estático configurado en `.env` |

---

## 2. Arquitectura objetivo

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Traefik v3.6  (puertos 80 / 443)                            │
│  • HTTP → HTTPS redirect automático                          │
│  • Let's Encrypt por subdominio                              │
│  • Descubrimiento de contenedores via Docker labels          │
└────┬──────────────┬───────────────┬──────────────────────────┘
     │              │               │
     ▼              ▼               ▼
meta.dom.com   colegio-a.dom   colegio-b.dom   …
     │              │               │
     ▼              ▼               ▼
 meta-admin     tenant-a app    tenant-b app
 (FastAPI)      (FastAPI)       (FastAPI)
 (SQLite)       (SQLite vol.)   (SQLite vol.)
```

Todos los contenedores se conectan a la red Docker externa `traefik_public`.
Traefik es el único componente que expone puertos al host.

---

## 3. Estructura de ficheros

```
school_matz/
│
├── backend/                    # App principal (sin cambios estructurales)
├── frontend/                   # App principal (sin cambios)
├── Dockerfile                  # Imagen school-matz:latest
│
├── traefik/
│   ├── traefik.yml             # Configuración estática de Traefik
│   └── acme.json               # Certificados Let's Encrypt (chmod 600, gitignored)
│
├── docker-compose.infra.yml    # Stack infraestructura: Traefik (+ meta-admin en Fase 3)
├── docker-compose.yml          # Stack app — modo legacy / desarrollo
│
├── docker/
│   ├── tenant-compose.yml.j2   # Plantilla Jinja2 para generar compose de cada tenant
│   ├── nginx.conf              # (legacy — solo para modo desarrollo local)
│   └── setup.sh                # (legacy — solo para modo desarrollo local)
│
├── meta-admin/                 # Aplicación de meta-administración (Fases 3-4)
│   ├── backend/
│   │   ├── main.py
│   │   ├── config.py           # Lee .env: BASE_DOMAIN, admin creds, SECRET_KEY
│   │   ├── database.py         # SQLite con SQLModel
│   │   ├── auth.py             # JWT para el único admin estático
│   │   ├── models.py           # Modelo Tenant
│   │   └── routers/
│   │       ├── auth.py         # POST /auth/login
│   │       ├── tenants.py      # CRUD + acciones (deploy/start/stop/destroy)
│   │       └── stats.py        # GET /tenants/{slug}/stats
│   ├── services/
│   │   ├── docker_service.py   # Renderiza plantilla, ejecuta docker compose
│   │   └── tenant_stats.py     # Lee SQLite del tenant para métricas
│   ├── frontend/
│   │   ├── login.html
│   │   ├── dashboard.html      # Lista de tenants + estadísticas
│   │   ├── tenant.html         # Detalle y gestión de un tenant
│   │   └── js/api.js
│   ├── data/                   # SQLite del meta-admin (gitignored)
│   ├── Dockerfile
│   └── .env.example
│
├── tenants/                    # Datos de tenants activos (gitignored)
│   └── {slug}/
│       ├── docker-compose.yml  # Generado por meta-admin
│       ├── .env                # Variables del tenant (gitignored)
│       ├── data/               # assets.db del tenant
│       └── static/             # Imágenes QR del tenant
│
└── scripts/
    ├── init-infra.sh           # Crea red traefik_public, acme.json, tenants/
    └── build-app-image.sh      # Construye school-matz:latest
```

---

## 4. Componentes clave

### 4.1 `traefik/traefik.yml`

Configuración estática. Puntos relevantes:
- `entryPoints.web` → redirección permanente a `websecure`
- `providers.docker.exposedByDefault: false` → solo contenedores con `traefik.enable=true`
- `providers.docker.network: traefik_public`
- `certificatesResolvers.letsencrypt` → httpChallenge en entrypoint `web`
- ⚠️ Cambiar `acme.email` por un email real antes del primer despliegue

### 4.2 `docker-compose.infra.yml`

Stack de infraestructura compartida. Levantarlo una vez, permanece activo:

```bash
docker compose -f docker-compose.infra.yml up -d
```

En Fase 3 se añade el servicio `meta-admin` a este fichero.

### 4.3 `docker/tenant-compose.yml.j2`

Plantilla Jinja2. Variables que recibe al renderizarse:

| Variable | Descripción |
|---|---|
| `tenant_slug` | Identificador único del tenant (`colegio-a`) |
| `base_domain` | Dominio raíz (`miescuela.es`) |
| `secret_key` | JWT secret generado aleatoriamente |

El fichero renderizado se escribe en `tenants/{slug}/docker-compose.yml`.

### 4.4 `backend/config.py` (app por tenant)

`qr_base_url` se construye automáticamente:
```
TENANT_SLUG=colegio-a  ──┐
BASE_DOMAIN=miescuela.es ─┴──→  qr_base_url = "https://colegio-a.miescuela.es"
```
Si se define `QR_BASE_URL` explícitamente en el `.env`, tiene prioridad.

### 4.5 Meta-admin: modelo de datos

```python
class Tenant(SQLModel, table=True):
    id:               int | None  # PK
    slug:             str         # subdominio + nombre de directorio
    nombre:           str         # nombre visible del centro
    base_domain:      str         # dominio base
    admin_username:   str         # superadmin del tenant
    estado:           str         # "creating" | "running" | "stopped" | "error"
    created_at:       datetime
    last_activity:    datetime | None   # último movimiento registrado
```

### 4.6 Meta-admin: autenticación

Un único administrador estático definido en `.env`:

```env
META_ADMIN_USERNAME=admin
META_ADMIN_PASSWORD_HASH=$2b$12$...    # bcrypt del password
META_SECRET_KEY=<64 bytes hex>
BASE_DOMAIN=miescuela.es
```

JWT de sesión con el mismo patrón que la app principal (`role: "meta-admin"`).

### 4.7 Meta-admin: endpoints principales

```
POST /auth/login                     → JWT
GET  /tenants                        → lista de tenants con estado
POST /tenants                        → crear y desplegar nuevo tenant
GET  /tenants/{slug}                 → detalle
POST /tenants/{slug}/start           → docker compose up
POST /tenants/{slug}/stop            → docker compose stop
DELETE /tenants/{slug}               → docker compose down + borrar directorio
GET  /tenants/{slug}/stats           → métricas leídas de la SQLite del tenant
```

### 4.8 Flujo de creación de un tenant

```
POST /tenants  { slug, nombre, admin_username, admin_password }
    │
    ├─ Valida: slug único, sin caracteres inválidos
    ├─ Crea directorio tenants/{slug}/data/ y tenants/{slug}/static/
    ├─ Genera SECRET_KEY aleatorio
    ├─ Renderiza docker/tenant-compose.yml.j2 → tenants/{slug}/docker-compose.yml
    ├─ Escribe registro en SQLite meta-admin (estado: "creating")
    ├─ Ejecuta: docker compose -f tenants/{slug}/docker-compose.yml up -d --wait
    ├─ Ejecuta: docker exec -e _ADMIN_USER=... -e _ADMIN_PASS=... tenant-{slug}
    │           python -c "..."  (crea el superadmin en la DB del tenant)
    │           Las credenciales se pasan como var. de entorno, nunca interpoladas
    ├─ Actualiza estado → "running"
    ├─ Actualiza estado → "running"
    └─ Traefik detecta el contenedor automáticamente y solicita cert Let's Encrypt
```

### 4.9 `docker_service.py` (meta-admin)

Accede al socket Docker montado como bind en el contenedor meta-admin:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
  - ./tenants:/app/tenants
```

Ejecuta `docker compose` como subproceso con `subprocess.run`, capturando stderr para reportar errores.

### 4.10 `tenant_stats.py` (meta-admin)

Lee directamente `tenants/{slug}/data/assets.db` con SQLite3 (mismo esquema que la app):
- Número de usuarios activos
- Número de items de material
- Movimientos en los últimos 30 días
- Timestamp del último movimiento (`last_activity`)

---

## 5. Fases de implementación

### Fase 1 — Infraestructura base ✅

**Objetivo:** Traefik corriendo, red compartida, app existente funcionando detrás de Traefik.

**Ficheros creados/modificados:**
- `scripts/init-infra.sh` — crea red `traefik_public`, `traefik/acme.json`, `tenants/`
- `traefik/traefik.yml` — config estática de Traefik
- `docker-compose.infra.yml` — Traefik como servicio (imagen `traefik:v3.6`)
- `docker-compose.yml` — eliminado nginx, añadidos Traefik labels, red → `traefik_public`

**Nota:** Requiere Traefik v3.6+. Docker Engine 29 subió la API mínima a 1.44, lo que rompía Traefik ≤ v3.5 (issue #12253, solucionado en v3.6 con auto-negociación de versión).

---

### Fase 2 — App parametrizable ✅

**Objetivo:** La app construye su `qr_base_url` desde variables de entorno, sin hardcodear el dominio. Imagen `school-matz:latest` disponible en el servidor.

**Ficheros creados/modificados:**
- `backend/config.py` — `qr_base_url` se construye como `https://{TENANT_SLUG}.{BASE_DOMAIN}` si no está definida explícitamente
- `.env.example` — sustituido `QR_BASE_URL` por `TENANT_SLUG` + `BASE_DOMAIN`
- `docker/tenant-compose.yml.j2` — plantilla Jinja2 para el compose de cada tenant
- `scripts/build-app-image.sh` — construye y etiqueta `school-matz:latest`

**Procedimiento:**
```bash
bash scripts/build-app-image.sh
# Opcionalmente con versión:
bash scripts/build-app-image.sh v1.0.0
```

---

### Fase 3 — Meta-admin backend ✅

**Objetivo:** API FastAPI para gestionar tenants: CRUD, despliegue, estadísticas.

**Ficheros creados:**
- `meta-admin/backend/main.py` — FastAPI app, registra routers, sirve frontend estático
- `meta-admin/backend/config.py` — pydantic-settings: `BASE_DOMAIN`, credenciales admin, `SECRET_KEY`
- `meta-admin/backend/database.py` — SQLAlchemy + SQLite en `data/meta.db`
- `meta-admin/backend/auth.py` — bcrypt + JWT (`role: "meta-admin"`, 8 h, HS256)
- `meta-admin/backend/models.py` — modelo `Tenant` con campos de estado
- `meta-admin/backend/routers/auth.py` — `POST /api/v1/auth/login`
- `meta-admin/backend/routers/tenants.py` — CRUD completo + acciones (deploy/start/stop/destroy)
- `meta-admin/backend/routers/stats.py` — `GET /api/v1/tenants/{slug}/stats`
- `meta-admin/services/docker_service.py` — renderiza plantilla Jinja2, ejecuta `docker compose`
- `meta-admin/services/tenant_stats.py` — lee SQLite del tenant para métricas
- `meta-admin/Dockerfile` — imagen `python:3.10-slim` + Poetry
- `meta-admin/.env.example`
- `meta-admin/pyproject.toml`

**Modificado:** `docker-compose.infra.yml` — servicio `meta-admin` con labels Traefik para `meta.{BASE_DOMAIN}`.

**Bugs corregidos durante pruebas:**
- `docker_service.py`: campo era `password_hash`, no `hashed_password`.
- Las credenciales del admin se inyectan como variables de entorno en `docker exec -e` en lugar de interpolarse en el código Python (seguridad).

**Resultado de pruebas (`curl`):**
```
POST /auth/login (credenciales correctas)  → 200 {access_token}
POST /auth/login (credenciales incorrectas) → 401 Credenciales incorrectas
GET  /tenants (con token)                  → 200 []
GET  /tenants (sin token)                  → 401 No autenticado
GET  /tenants/noexiste/stats               → 404 Tenant no encontrado
POST /tenants slug="INVALIDO!!"            → 422 (validación Pydantic)
```

---

### Fase 4 — Meta-admin frontend ✅

**Objetivo:** Interfaz HTML + JS para gestionar tenants desde el navegador.

**Ficheros creados:**
- `meta-admin/frontend/index.html` — redirección inmediata a `/dashboard.html`
- `meta-admin/frontend/login.html` — formulario de acceso; redirige al dashboard si ya hay token
- `meta-admin/frontend/dashboard.html` — tabla de tenants con badge de estado (`running / stopped / creating / error`), botones ▶/⏸/🗑 por fila, modal "Nuevo centro" con validación, toast de notificaciones
- `meta-admin/frontend/tenant.html` — detalle de un centro: info general, tarjetas de estadísticas (usuarios activos, material, movimientos 30 d, último movimiento), acciones start/stop/eliminar con modal de confirmación
- `meta-admin/frontend/js/api.js` — `metaFetch()` con auth guard (→ `/login.html` en 401), objeto `api` con todos los endpoints (`login`, `getTenants`, `getTenant`, `createTenant`, `startTenant`, `stopTenant`, `deleteTenant`, `getStats`)

**Flujo de navegación:**
```
/  →  /dashboard.html  (auth guard → /login.html si no hay token)
               ↓ click "Ver"
         /tenant.html?slug=xxx
               ↓ "Eliminar"
         /dashboard.html
```

**Estilo:** Tailwind CSS (CDN), sin frameworks JS, vanilla DOM.

---

### Fase 5 — Integración y documentación final ✅

**Objetivo:** Todo funcionando end-to-end, documentación actualizada.

**Completado:**
- `README.md` — añadida sección "Modo Multitenant" con pasos de puesta en marcha y enlace a `MULTI_TENANT.md`
- `DOCKER_DEPLOYMENT.md` — añadida sección 14 "Despliegue Multitenant" con tabla comparativa, primer despliegue, actualización de tenants y backup multitenant
- `.gitignore` — añadidas entradas: `tenants/`, `meta-admin/data/`, `traefik/acme.json`

---

## 6. Procedimientos operacionales

### Primer despliegue en servidor nuevo

```bash
# 1. Clonar repositorio
git clone ... && cd school_matz

# 2. Crear infraestructura base (una sola vez)
bash scripts/init-infra.sh

# 3. Configurar Traefik
#    Editar traefik/traefik.yml → poner email real en acme.email

# 4. Configurar meta-admin
cp meta-admin/.env.example meta-admin/.env
# Editar meta-admin/.env: BASE_DOMAIN, META_ADMIN_USERNAME, META_ADMIN_PASSWORD_HASH

# 5. Construir imagen de la app
bash scripts/build-app-image.sh

# 6. Levantar Traefik + meta-admin
docker compose -f docker-compose.infra.yml up -d
```

### Actualizar la app (nueva versión para todos los tenants)

```bash
# Reconstruir imagen
bash scripts/build-app-image.sh v1.x.x

# Actualizar cada tenant (requiere recrear el contenedor para usar nueva imagen)
# Desde el meta-admin (interfaz web) → botón "Actualizar"
# O manualmente:
docker compose -f tenants/<slug>/docker-compose.yml up -d --force-recreate
```

### Backup de un tenant

```bash
# La base de datos es un fichero en el host:
cp -r tenants/<slug>/data/ backups/<slug>-$(date +%Y%m%d)/
```
