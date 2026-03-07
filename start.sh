#!/usr/bin/env bash
# start.sh — Arranca el servidor School Assets en modo desarrollo/producción local.
# Uso: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

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
echo "  (Nginx expone https://materiales.local)"
echo ""
echo "  Para parar: Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
