#!/usr/bin/env bash
# first_run.sh — Setup interactivo del primer arranque (modo sin Docker).
# Configura dominio, certificado SSL y nginx.
#
# Uso: sudo bash scripts/first_run.sh
# (requiere sudo para instalar paquetes y escribir en /etc/nginx/)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/domain"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🏫 School Assets — Configuración inicial"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Este asistente configura:"
echo "   1. El dominio local bajo el que se servirá la aplicación"
echo "   2. El certificado HTTPS (mkcert) para ese dominio"
echo "   3. Nginx como proxy inverso"
echo "   4. El superadministrador del panel de administración"
echo ""

# ── 1. Dominio ────────────────────────────────────────────────────────────────
CURRENT_DOMAIN=""
if [[ -f "$CONFIG_FILE" ]]; then
  CURRENT_DOMAIN="$(tr -d '[:space:]' < "$CONFIG_FILE")"
fi

DEFAULT="${CURRENT_DOMAIN:-materiales.local}"

echo -n "  Dominio [${DEFAULT}]: "
read -r INPUT_DOMAIN
DOMAIN="${INPUT_DOMAIN:-$DEFAULT}"

# Validación básica: sin espacios, sin http://, longitud razonable
if [[ "$DOMAIN" =~ [[:space:]] || "$DOMAIN" =~ ^https?:// || ${#DOMAIN} -gt 253 ]]; then
  echo "  ❌ Dominio no válido: '${DOMAIN}'"
  echo "     Usa un nombre como 'materiales.local' o 'assets.miescuela.es'"
  exit 1
fi

# Guardar dominio
mkdir -p "$SCRIPT_DIR/config"
printf '%s\n' "$DOMAIN" > "$CONFIG_FILE"
echo "  ✅ Dominio guardado: $DOMAIN"
echo ""

# ── 2. Certificado SSL ────────────────────────────────────────────────────────
echo "  ¿Instalar certificado mkcert (recomendado) o autofirmado?"
echo "  mkcert evita las advertencias de seguridad en el navegador."
echo ""
echo -n "  Tipo de certificado [mkcert/autofirmado] (mkcert): "
read -r CERT_TYPE
CERT_TYPE="${CERT_TYPE:-mkcert}"

if [[ "$CERT_TYPE" == "mkcert" ]]; then
  echo ""
  echo "→ Ejecutando setup_mkcert.sh…"
  bash "$SCRIPT_DIR/scripts/setup_mkcert.sh" "$DOMAIN"
else
  echo ""
  echo "→ Generando certificado autofirmado…"
  bash "$SCRIPT_DIR/scripts/gen_cert.sh" "$DOMAIN"
fi

# ── 3. Nginx ──────────────────────────────────────────────────────────────────
echo ""
echo "→ Configurando nginx…"
bash "$SCRIPT_DIR/scripts/setup_nginx.sh" "$DOMAIN"

# ── 4. Superadministrador ─────────────────────────────────────────────────────
echo ""
echo "→ Configurando el superadministrador…"
bash "$SCRIPT_DIR/scripts/prepare_root.sh"

# ── 5. Resumen ────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Configuración inicial completada."
echo ""
echo "  Dominio:     ${DOMAIN}"
echo "  Certificado: $SCRIPT_DIR/certs/app.crt"
echo "  Acceso:      https://${DOMAIN}"
echo ""
echo "  Arranca la aplicación con:"
echo "    ./start.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
