# Arranque y parada del stack

Guía rápida para los tres modos de ejecución.

---

## Modo 1 — Usuario único en local (sin multitenant)

Arranca **nginx (SSL) + la aplicación**. Sin Traefik ni meta-admin.
Útil para instalación en un solo centro con acceso desde móviles y tablets.

### Servicios que arranca

| Contenedor | Descripción |
|---|---|
| `school-assets-nginx` | Nginx — termina el SSL, redirige HTTP→HTTPS |
| `school-assets-app` | La aplicación FastAPI |

### Prerrequisitos del sistema host

- **avahi-daemon** configurado con `host-name=materiales` y `domain-name=local`
  en `/etc/avahi/avahi-daemon.conf` → resuelve `materiales.local` en toda la WiFi
- Puerto **80** y **443** libres en el host
- **openssl** disponible (para generar certs)

### Primera puesta en marcha

```bash
# 1. Copia y edita el .env
cp .env.example .env
# Ajusta SECRET_KEY (obligatorio). El resto de valores tienen defaults válidos.

# 2. Genera la CA local y el certificado del servidor (solo la primera vez)
bash scripts/gen-certs-standalone.sh
#    Crea:  certs/standalone/ca.crt      ← instalar en dispositivos
#           certs/standalone/server.crt  ← montado en nginx automáticamente
#           certs/standalone/server.key

# 3. Construye la imagen (solo si no existe o hay cambios de código)
docker build -t school-matz:latest .

# 4. Levanta nginx + app
docker compose -f docker-compose.standalone.yml up -d

# 5. Crea el primer administrador
docker exec -it school-assets-app bash scripts/prepare_root.sh
```

### Arranque habitual (tras la primera puesta en marcha)

```bash
docker compose -f docker-compose.standalone.yml up -d
```

### Parada

```bash
docker compose -f docker-compose.standalone.yml down
```

### Acceso

| URL | Descripción |
|---|---|
| `https://materiales.local` | Aplicación principal |
| `https://materiales.local/admin` | Administración |
| `http://materiales.local/ca.crt` | Descarga del certificado CA (HTTP para poder descargarlo antes de instalarlo) |

> **Resolución DNS automática:** todos los dispositivos de la misma red WiFi
> resuelven `materiales.local` sin configuración adicional gracias a avahi mDNS.

### Instalar el certificado CA en dispositivos

Los navegadores móviles bloquean HTTPS con certificados autofirmados.
Instala `certs/standalone/ca.crt` una vez en cada dispositivo:

**Android**
1. Abre `http://materiales.local/ca.crt` en el navegador del dispositivo
   (Android detecta el tipo y lanza el instalador automáticamente)
2. O cópialo por USB/email → *Ajustes → Seguridad → Instalar certificado →
   Certificado de CA*

**iOS / iPadOS**
1. Envía `ca.crt` por email o AirDrop al dispositivo
2. *Ajustes → General → VPN y gestión de dispositivos → instalar perfil*
3. *Ajustes → General → Información → Conf. de confianza de certificados →
   activa el switch del certificado*

**Navegador de escritorio (Linux/Windows/Mac)**
Importa `ca.crt` en la sección de certificados del navegador o del sistema.

---

## Modo 2 — Multitenant en local (desarrollo)

Arranca Traefik (HTTP, sin TLS) + meta-admin. Los tenants se crean desde
la UI del meta-admin y se accede a ellos por subdominio.

### Prerrequisito único (ejecutar una sola vez)

```bash
# Red Docker compartida + directorio tenants/
bash scripts/init-infra.sh

# Copia y edita el .env local del meta-admin
cp meta-admin/.env.example meta-admin/.env.local
# Edita meta-admin/.env.local:
#   BASE_DOMAIN=local.test
#   META_ADMIN_USERNAME=admin
#   META_ADMIN_PASSWORD_HASH=  ← genera con:
#     python3 -c "import bcrypt; print(bcrypt.hashpw(b'tupass', bcrypt.gensalt()).decode())"
#   META_SECRET_KEY=           ← genera con:
#     python3 -c "import secrets; print(secrets.token_hex(32))"

# Resolución DNS wildcard *.local.test → IP LAN (requiere sudo)
bash scripts/setup-dnsmasq-local.sh
```

> **Dispositivos Android en la misma WiFi:**
> Configura su DNS primario con la IP LAN que muestra el script (ej. `192.168.1.x`).
> Después podrán acceder a cualquier tenant sin configuración adicional.

### Arranque

```bash
docker compose -f docker-compose.infra.local.yml up -d --remove-orphans
```

| URL | Descripción |
|-----|-------------|
| `http://meta.local.test` | Panel de gestión de tenants |
| `http://meta.local.test/dashboard.html` | Dashboard |
| `http://localhost:8001` | Acceso directo al meta-admin (sin Traefik) |
| `http://localhost:8080` | Dashboard de Traefik |
| `http://<slug>.local.test` | Panel del tenant |

### Crear un tenant

1. Abre `http://meta.local.test/dashboard.html`
2. Haz clic en **Nuevo centro** y rellena el formulario
3. El contenedor del tenant arranca automáticamente
4. Accede en `http://<slug>.local.test`

### Parada

```bash
docker compose -f docker-compose.infra.local.yml down
```

Para parar también todos los tenants:

```bash
docker compose -f docker-compose.infra.local.yml down
docker ps --filter name=tenant- --format "{{.Names}}" | xargs -r docker stop
```

---

## Modo 3 — Multitenant en VPS (producción)

Arranca Traefik (HTTP + HTTPS con Let's Encrypt automático) + meta-admin.
Los tenants se crean desde la UI y reciben certificado TLS en segundos.

### Prerrequisitos

- VPS con Docker y Docker Compose instalados
- Dominio real con wildcard DNS apuntando al VPS:
  ```
  A    *.tudominio.es  →  IP_del_VPS
  A    tudominio.es    →  IP_del_VPS
  meta.tudominio.es    →  IP_del_VPS  (o cubre el wildcard)
  ```
- Puertos **80** y **443** abiertos en el firewall del VPS

### Preparación inicial (ejecutar una sola vez en el VPS)

```bash
# 1. Clona el repositorio (o sube los ficheros)
git clone <repo> school_matz && cd school_matz

# 2. Infraestructura base
bash scripts/init-infra.sh

# 3. Configura Traefik — pon tu email real en acme.email
nano traefik/traefik.yml

# 4. Copia y edita el .env del meta-admin
cp meta-admin/.env.example meta-admin/.env
# Edita meta-admin/.env:
#   BASE_DOMAIN=tudominio.es
#   META_ADMIN_USERNAME=admin
#   META_ADMIN_PASSWORD_HASH=  ← genera con python3 + bcrypt
#   META_SECRET_KEY=           ← genera con secrets.token_hex(32)
```

### Arranque

```bash
docker compose -f docker-compose.infra.yml up -d
```

| URL | Descripción |
|-----|-------------|
| `https://meta.tudominio.es` | Panel de gestión de tenants |
| `https://meta.tudominio.es/dashboard.html` | Dashboard |
| `https://<slug>.tudominio.es` | Panel del tenant |

> TLS se emite automáticamente por Let's Encrypt al primer acceso.

### Crear un tenant

1. Abre `https://meta.tudominio.es/dashboard.html`
2. **Nuevo centro** → rellena slug, nombre y credenciales del administrador
3. El contenedor arranca y Traefik emite el certificado automáticamente

### Parada

```bash
# Solo la infraestructura (Traefik + meta-admin)
docker compose -f docker-compose.infra.yml down

# Todos los tenants también
docker ps --filter name=tenant- --format "{{.Names}}" | xargs -r docker stop
```

### Actualizar la imagen de la app tras un cambio de código

```bash
# Reconstruir y subir la imagen
docker build -t school-matz:latest .

# Reiniciar todos los contenedores de tenant para que usen la nueva imagen
docker ps --filter name=tenant- --format "{{.Names}}" | \
  xargs -I{} sh -c 'docker stop {} && docker rm {} && \
    docker compose -f /ruta/tenants/$(echo {} | sed s/tenant-//)/docker-compose.yml up -d'
```

---

## Resumen de ficheros clave

| Fichero | Uso |
|---------|-----|
| `docker-compose.standalone.yml` | App en modo usuario único (puerto 8080) |
| `docker-compose.infra.local.yml` | Infraestructura multitenant local |
| `docker-compose.infra.yml` | Infraestructura multitenant producción |
| `traefik/traefik-local.yml` | Config Traefik local (HTTP, sin ACME) |
| `traefik/traefik.yml` | Config Traefik producción (HTTPS + ACME) |
| `meta-admin/.env.local` | Variables del meta-admin en local (gitignored) |
| `meta-admin/.env` | Variables del meta-admin en producción (gitignored) |
| `scripts/init-infra.sh` | Inicialización única de infraestructura |
| `scripts/setup-dnsmasq-local.sh` | Configura DNS wildcard local |
