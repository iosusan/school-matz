#!/usr/bin/env bash
# Genera un certificado SSL autofirmado válido para materiales.local
# Solo necesita ejecutarse una vez.

set -e

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$CERT_DIR/materiales.key" \
  -out    "$CERT_DIR/materiales.crt" \
  -days   3650 \
  -subj   "/CN=materiales.local" \
  -addext "subjectAltName=DNS:materiales.local,DNS:localhost,IP:127.0.0.1"

echo ""
echo "✅ Certificado generado en $CERT_DIR/"
echo ""
echo "En el móvil, la primera vez que accedas a https://materiales.local"
echo "verás un aviso de seguridad. Pulsa 'Avanzado' → 'Aceptar riesgo y continuar'."
