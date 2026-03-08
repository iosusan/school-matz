#!/usr/bin/env bash
# scripts/gen-certs-standalone.sh
# ─────────────────────────────────────────────────────────────
# Genera un certificado SSL autofirmado para materiales.local.
# Crea una mini-CA local para que el certificado sea instalable
# en dispositivos Android/iOS como autoridad de confianza.
#
# Salida:
#   certs/standalone/ca.crt       ← instalar en Android/iOS
#   certs/standalone/server.crt   ← cert del servidor (nginx)
#   certs/standalone/server.key   ← clave privada (nginx)
#
# Uso:
#   bash scripts/gen-certs-standalone.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

DOMAIN="materiales.local"
OUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs/standalone"
DAYS=3650

# Detectar IP LAN (primera IP no-loopback)
LAN_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if ($i=="src") print $(i+1)}' | head -1)
LAN_IP=${LAN_IP:-127.0.0.1}

echo "→ Dominio : $DOMAIN"
echo "→ IP LAN  : $LAN_IP"
echo "→ Destino : $OUT_DIR"

mkdir -p "$OUT_DIR"

# ── 1. Generar CA (root) ────────────────────────────────────
if [[ ! -f "$OUT_DIR/ca.key" ]]; then
  echo ""
  echo "[ 1/5 ] Generando clave CA..."
  openssl genrsa -out "$OUT_DIR/ca.key" 4096 2>/dev/null
fi

if [[ ! -f "$OUT_DIR/ca.crt" ]]; then
  echo "[ 2/5 ] Generando certificado CA (válido $DAYS días)..."
  openssl req -x509 -new -nodes \
    -key "$OUT_DIR/ca.key" \
    -sha256 -days "$DAYS" \
    -out "$OUT_DIR/ca.crt" \
    -subj "/CN=materiales-local-CA/O=School Matz Local CA" 2>/dev/null
fi

# ── 2. Generar clave del servidor ───────────────────────────
echo "[ 3/5 ] Generando clave del servidor..."
openssl genrsa -out "$OUT_DIR/server.key" 2048 2>/dev/null

# ── 3. Generar CSR con SAN ──────────────────────────────────
echo "[ 4/5 ] Generando CSR con Subject Alt Names..."
openssl req -new \
  -key "$OUT_DIR/server.key" \
  -out "$OUT_DIR/server.csr" \
  -subj "/CN=$DOMAIN" 2>/dev/null

# ── 4. Firmar con la CA incluyendo SAN ─────────────────────
echo "[ 5/5 ] Firmando certificado del servidor..."
openssl x509 -req \
  -in "$OUT_DIR/server.csr" \
  -CA "$OUT_DIR/ca.crt" \
  -CAkey "$OUT_DIR/ca.key" \
  -CAcreateserial \
  -out "$OUT_DIR/server.crt" \
  -days "$DAYS" -sha256 \
  -extfile <(cat <<EOF
subjectAltName=DNS:$DOMAIN,IP:$LAN_IP,IP:127.0.0.1
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
EOF
) 2>/dev/null

rm -f "$OUT_DIR/server.csr" "$OUT_DIR/ca.srl"

echo ""
echo "✓ Certificados generados en: $OUT_DIR/"
echo ""
echo "  server.crt / server.key → montados en nginx (automático)"
echo "  ca.crt                  → INSTALAR en dispositivos Android/iOS"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo " INSTALAR ca.crt en Android:"
echo "   1. Copia el fichero al dispositivo (USB, email, etc.)"
echo "   2. Ajustes → Seguridad → Instalar certificado"
echo "      (o Ajustes → Biometría y seguridad → Otros ajustes de seguridad)"
echo "   3. Selecciona 'Certificado de CA' o 'Certificado VPN y aplicaciones'"
echo "   4. Elige el fichero ca.crt"
echo "─────────────────────────────────────────────────────────────"
echo " INSTALAR ca.crt en iOS/iPadOS:"
echo "   1. Envía el archivo por email o AirDrop al dispositivo"
echo "   2. Ajustes → General → VPN y gestión de dispositivos → instalar perfil"
echo "   3. Ajustes → General → Información → Conf. de confianza de certificados"
echo "      → activa el switch del certificado"
echo "─────────────────────────────────────────────────────────────"
