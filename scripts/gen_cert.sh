#!/usr/bin/env bash
# Genera un certificado SSL autofirmado para el dominio configurado.
# Uso: [sudo] bash scripts/gen_cert.sh [dominio]
# Si no se pasa dominio, lee config/domain. Si tampoco existe, usa materiales.local.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$SCRIPT_DIR/certs"

# ── Determinar dominio ──────────────────────────────────────────────────
DOMAIN="${1:-}"
if [[ -z "$DOMAIN" && -f "$SCRIPT_DIR/config/domain" ]]; then
  DOMAIN="$(tr -d '[:space:]' < "$SCRIPT_DIR/config/domain")"
fi
DOMAIN="${DOMAIN:-materiales.local}"

mkdir -p "$CERT_DIR"
echo "→ Generando certificado autofirmado para '${DOMAIN}'…"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$CERT_DIR/app.key" \
  -out    "$CERT_DIR/app.crt" \
  -days   3650 \
  -subj   "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"

echo ""
echo "✅ Certificado generado en $CERT_DIR/"
echo ""
echo "En el móvil, la primera vez que accedas a https://${DOMAIN}"
echo "verás un aviso de seguridad. Pulsa 'Avanzado' → 'Aceptar riesgo y continuar'."
