#!/usr/bin/env bash
# docker/setup.sh — Configuración inicial para despliegue Docker.
# Ejecutar UNA VEZ antes del primer "docker compose up".
#
# Uso: bash docker/setup.sh [dominio]
# (No requiere sudo — los certs se generan en ./certs/ del proyecto)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/domain"
TEMPLATE="$SCRIPT_DIR/docker/nginx.conf.template"
NGINX_CONF="$SCRIPT_DIR/docker/nginx.conf"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🐳 School Assets Docker — Configuración inicial"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Dominio ────────────────────────────────────────────────────────────────
DOMAIN="${1:-}"

if [[ -z "$DOMAIN" ]]; then
  CURRENT_DOMAIN=""
  if [[ -f "$CONFIG_FILE" ]]; then
    CURRENT_DOMAIN="$(tr -d '[:space:]' < "$CONFIG_FILE")"
  fi
  DEFAULT="${CURRENT_DOMAIN:-materiales.local}"

  echo -n "  Dominio [${DEFAULT}]: "
  read -r INPUT_DOMAIN
  DOMAIN="${INPUT_DOMAIN:-$DEFAULT}"
fi

# Validación básica
if [[ "$DOMAIN" =~ [[:space:]] || "$DOMAIN" =~ ^https?:// || ${#DOMAIN} -gt 253 ]]; then
  echo "  ❌ Dominio no válido: '${DOMAIN}'"
  echo "     Usa un nombre como 'materiales.local' o 'assets.miescuela.es'"
  exit 1
fi

mkdir -p "$SCRIPT_DIR/config"
printf '%s\n' "$DOMAIN" > "$CONFIG_FILE"
echo "  ✅ Dominio: $DOMAIN"
echo ""

# ── 2. Certificado SSL ────────────────────────────────────────────────────────
# El certificado se genera en el host con mkcert y se monta como bind en el
# contenedor nginx (./certs → /certs). El contenedor NO necesita mkcert.

if [[ -f "$SCRIPT_DIR/certs/app.crt" && -f "$SCRIPT_DIR/certs/app.key" ]]; then
  echo "  ✅ Certificado existente: $SCRIPT_DIR/certs/app.crt"
  echo -n "  ¿Regenerar certificado para '${DOMAIN}'? [s/N]: "
  read -r REGEN
  if [[ "${REGEN,,}" != "s" ]]; then
    echo "  → Reutilizando certificado existente."
  else
    _gen_cert=true
  fi
else
  _gen_cert=true
fi

if [[ "${_gen_cert:-false}" == "true" ]]; then
  if command -v mkcert &>/dev/null; then
    echo "→ Generando certificado mkcert para '${DOMAIN}'…"
    CERT_DIR="$SCRIPT_DIR/certs"
    CAROOT="$CERT_DIR/ca"
    mkdir -p "$CAROOT" "$CERT_DIR"

    # setup_mkcert.sh se ejecuta con sudo, dejando certs/ (y certs/ca/)
    # propiedad de root. Corregir toda la carpeta certs/ para que mkcert
    # pueda leer rootCA-key.pem y cp pueda escribir rootCA.pem.
    if [[ -d "$CERT_DIR" ]] && [[ "$(stat -c '%U' "$CERT_DIR")" != "$(id -un)" || \
        ( -f "$CAROOT/rootCA-key.pem" && ! -r "$CAROOT/rootCA-key.pem" ) || \
        ( -f "$CERT_DIR/rootCA.pem"   && ! -w "$CERT_DIR/rootCA.pem"   ) ]]; then
      echo "  → Ajustando permisos de certs/ (requiere sudo)…"
      sudo chown -R "$(id -un)" "$CERT_DIR"
    fi

    CAROOT="$CAROOT" mkcert -install
    CA_PEM="$(CAROOT="$CAROOT" mkcert -CAROOT)/rootCA.pem"
    cp "$CA_PEM" "$CERT_DIR/rootCA.pem"
    chmod o+r "$CERT_DIR/rootCA.pem"
    cd "$CERT_DIR"
    CAROOT="$CAROOT" mkcert \
      -cert-file app.crt \
      -key-file  app.key \
      "${DOMAIN}" localhost 127.0.0.1
    echo "  ✅ Certificado mkcert generado."
  else
    echo "→ mkcert no encontrado. Generando certificado autofirmado…"
    echo "  (para mkcert, instala con: sudo bash scripts/setup_mkcert.sh)"
    bash "$SCRIPT_DIR/scripts/gen_cert.sh" "$DOMAIN"
    echo "  ✅ Certificado autofirmado generado."
  fi
fi

# ── 3. Generar nginx.conf desde plantilla ───────────────────────────────────
echo "→ Generando docker/nginx.conf para '${DOMAIN}'…"
sed "s|__DOMAIN__|${DOMAIN}|g" "$TEMPLATE" > "$NGINX_CONF"
echo "  ✅ docker/nginx.conf generado."

# ── 4. Secret key para JWT ──────────────────────────────────────────────────
if grep -q '^SECRET_KEY=' "$SCRIPT_DIR/.env" 2>/dev/null; then
  echo "  ✅ SECRET_KEY ya existe en .env"
else
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
    || head -c 32 /dev/urandom | od -A n -t x1 | tr -d ' \n')
  printf '\nSECRET_KEY=%s\n' "$SECRET_KEY" >> "$SCRIPT_DIR/.env"
  echo "  ✅ SECRET_KEY generada y guardada en .env"
fi

# ── 5. Resumen ────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Configuración Docker lista."
echo ""
echo "  Dominio:     ${DOMAIN}"
echo "  Acceso:      https://${DOMAIN}"
echo ""
echo "  Pasos para arrancar:"
echo "    1. docker compose up --build -d"
echo "    2. docker exec -it school-assets-app bash scripts/prepare_root.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
