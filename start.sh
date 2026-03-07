#!/usr/bin/env bash
# start.sh — Arranca el servidor School Assets en modo desarrollo/producción local.
# Uso: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Primer arranque ───────────────────────────────────────────────────────────
if [[ ! -f "$SCRIPT_DIR/config/domain" ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  ⚠️  Primera ejecución detectada."
  echo ""
  echo "  Ejecuta primero el asistente de configuración inicial:"
  echo "    sudo bash scripts/first_run.sh"
  echo ""
  echo "  Configura el dominio, el certificado HTTPS y nginx."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi

DOMAIN="$(tr -d '[:space:]' < "$SCRIPT_DIR/config/domain")"

# Activar entorno virtual Poetry si no está activo ya
if [ -z "$VIRTUAL_ENV" ]; then
  source .venv/bin/activate
fi

# Crear directorio de datos si no existe
mkdir -p data static/qr

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🏫 School Assets — Arrancando..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  API + Frontend: http://localhost:8000"
echo "  Nginx expone:   https://${DOMAIN}"
echo ""
echo "  Para parar: Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
