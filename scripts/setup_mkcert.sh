#!/usr/bin/env bash
# Instala mkcert, crea una CA local y genera un certificado válido
# para materiales.local. El root CA debe instalarse en cada dispositivo
# para que el navegador no muestre advertencias de seguridad.
#
# Uso: sudo bash scripts/setup_mkcert.sh
#
# Tras ejecutar este script:
#  - Los certificados quedan en ./certs/
#  - El root CA para instalar en móviles está en ./certs/rootCA.pem
#  - Nginx se recarga automáticamente si está activo

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$PROJECT_DIR/certs"
NGINX_CONF=/etc/nginx/sites-available/materiales

# ── 1. Instalar dependencias ──────────────────────────────────────────────────
echo "→ Instalando libnss3-tools (necesario para mkcert)…"
apt-get update -qq && apt-get install -y libnss3-tools wget

# ── 2. Instalar mkcert ────────────────────────────────────────────────────────
if ! command -v mkcert &>/dev/null; then
  echo "→ Descargando mkcert…"
  ARCH=$(dpkg --print-architecture)
  case "$ARCH" in
    amd64) MKCERT_BIN="mkcert-v1.4.4-linux-amd64" ;;
    arm64) MKCERT_BIN="mkcert-v1.4.4-linux-arm64" ;;
    arm)   MKCERT_BIN="mkcert-v1.4.4-linux-arm"   ;;
    *)     echo "Arquitectura no soportada: $ARCH"; exit 1 ;;
  esac
  wget -q "https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/${MKCERT_BIN}" \
    -O /usr/local/bin/mkcert
  chmod +x /usr/local/bin/mkcert
  echo "   mkcert instalado en /usr/local/bin/mkcert"
else
  echo "   mkcert ya está instalado ($(mkcert --version 2>&1 || true))"
fi

# ── 3. Instalar el root CA en el almacén del sistema ─────────────────────────
# CAROOT dentro del proyecto para que sea fácil de exportar al móvil
CAROOT="$CERT_DIR/ca"
mkdir -p "$CAROOT"

echo "→ Creando CA local en $CAROOT …"
CAROOT="$CAROOT" mkcert -install

# Copiar el rootCA.pem al directorio certs/ para distribución fácil
CA_PEM="$(CAROOT="$CAROOT" mkcert -CAROOT)/rootCA.pem"
cp "$CA_PEM" "$CERT_DIR/rootCA.pem"
# Permisos para que nginx (www-data) pueda leer el fichero
chmod o+x /home/iosu /home/iosu/projects /home/iosu/projects/school_matz "$CERT_DIR"
chmod o+r "$CERT_DIR/rootCA.pem"
echo "   Root CA copiado en $CERT_DIR/rootCA.pem"

# ── 4. Generar certificado para materiales.local ──────────────────────────────
echo "→ Generando certificado para materiales.local…"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

CAROOT="$CAROOT" mkcert \
  -cert-file materiales.crt \
  -key-file  materiales.key \
  materiales.local localhost 127.0.0.1

echo "   Certificado generado: $CERT_DIR/materiales.crt"

# ── 5. Recargar nginx si está activo ─────────────────────────────────────────
if systemctl is-active --quiet nginx; then
  nginx -t && systemctl reload nginx
  echo "→ Nginx recargado con el nuevo certificado."
else
  echo "   (nginx no está activo, omitiendo recarga)"
fi

# ── 6. Instrucciones de instalación del root CA ───────────────────────────────
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Certificado mkcert instalado correctamente."
echo ""
echo "  Para eliminar las advertencias de seguridad en cada dispositivo,"
echo "  instala el root CA una sola vez:"
echo ""
echo "  URL de descarga (desde cualquier dispositivo en la misma WiFi):"
echo "  👉  http://materiales.local/rootCA.pem"
echo ""
echo "  ── Android ─────────────────────────────────────────────────────"
echo "  Usa Firefox para Android (Chrome ignora CAs de usuario):"
echo "  1. Descarga rootCA.pem desde http://materiales.local/rootCA.pem"
echo "  2. Ajustes del sistema → Seguridad → Instalar certificado → CA"
echo "  3. En Firefox: about:config → security.enterprise_roots.enabled = true"
echo ""
echo "  ── iOS / iPadOS ───────────────────────────────────────────────"
echo "  1. Abre Safari y descarga http://materiales.local/rootCA.pem"
echo "  2. Ajustes → General → VPN y gestión del dispositivo → Instalar"
echo "  3. Ajustes → General → Información → Conf. de confianza de certificados"
echo "     → Activa 'mkcert …' como certificado raíz de confianza completa"
echo ""
echo "  ── Windows / Mac ──────────────────────────────────────────────"
echo "  Ejecutar en el PC: CAROOT=$CAROOT mkcert -install"
echo "════════════════════════════════════════════════════════════════"
