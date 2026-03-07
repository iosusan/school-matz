#!/usr/bin/env bash
# Instala nginx y lo configura como proxy inverso para school-assets.
# Lee el dominio desde config/domain.
# Ejecutar con: sudo bash scripts/setup_nginx.sh [dominio]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── Determinar dominio ────────────────────────────────────────────────────────
DOMAIN="${1:-}"
if [[ -z "$DOMAIN" && -f "$SCRIPT_DIR/config/domain" ]]; then
  DOMAIN="$(tr -d '[:space:]' < "$SCRIPT_DIR/config/domain")"
fi
DOMAIN="${DOMAIN:-materiales.local}"

echo "→ Instalando nginx…"
apt-get update -qq && apt-get install -y nginx

echo "→ Comprobando certificado SSL…"
if [[ -f "$SCRIPT_DIR/certs/app.crt" && -f "$SCRIPT_DIR/certs/rootCA.pem" ]]; then
  echo "   Certificado mkcert ya existe ($SCRIPT_DIR/certs/app.crt)."
elif [[ -f "$SCRIPT_DIR/certs/app.crt" ]]; then
  echo "   Certificado autofirmado ya existe."
  echo "   Para mejorar la experiencia en móviles, ejecuta después:"
  echo "     sudo bash scripts/setup_mkcert.sh"
else
  echo "   Certificado no encontrado, generando autofirmado…"
  bash "$SCRIPT_DIR/scripts/gen_cert.sh" "$DOMAIN"
  echo ""
  echo "   ⚠️  El navegador mostrará una advertencia de seguridad."
  echo "   Para eliminarla, ejecuta después: sudo bash scripts/setup_mkcert.sh"
fi

echo "→ Generando configuración nginx para '${DOMAIN}'…"
sed \
  -e "s|__DOMAIN__|${DOMAIN}|g" \
  -e "s|__PROJECT_DIR__|${SCRIPT_DIR}|g" \
  "$SCRIPT_DIR/scripts/nginx-materiales.conf" \
  > /etc/nginx/sites-available/materiales

# Activar el sitio
if [[ ! -L /etc/nginx/sites-enabled/materiales ]]; then
  ln -s /etc/nginx/sites-available/materiales /etc/nginx/sites-enabled/materiales
fi

# Desactivar el sitio por defecto si existe para evitar conflicto con el puerto 80
if [[ -L /etc/nginx/sites-enabled/default ]]; then
  rm /etc/nginx/sites-enabled/default
  echo "   (sitio 'default' de nginx desactivado)"
fi

echo "→ Verificando configuración de nginx…"
nginx -t

echo "→ Activando y arrancando nginx…"
systemctl enable nginx
systemctl reload nginx

echo ""
echo "✅ Nginx configurado."
echo "   https://${DOMAIN} → proxy a FastAPI en puerto 8000"
