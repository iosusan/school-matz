#!/usr/bin/env bash
# scripts/build-app-image.sh — Construye y etiqueta la imagen school-matz:latest.
# Ejecutar desde la raíz del proyecto cada vez que se quiera publicar
# una nueva versión de la app para que los tenants la usen.
#
# Uso:
#   bash scripts/build-app-image.sh          # etiqueta como latest
#   bash scripts/build-app-image.sh v1.2.0   # etiqueta como latest + v1.2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="school-matz"
TAG="${1:-}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🐳 Construyendo imagen ${IMAGE_NAME}:latest"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$SCRIPT_DIR"

docker build \
  --tag "${IMAGE_NAME}:latest" \
  --file Dockerfile \
  .

echo "  ✅ Imagen construida: ${IMAGE_NAME}:latest"

# Etiqueta adicional si se pasó una versión
if [[ -n "$TAG" ]]; then
  docker tag "${IMAGE_NAME}:latest" "${IMAGE_NAME}:${TAG}"
  echo "  ✅ Etiqueta adicional: ${IMAGE_NAME}:${TAG}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Imagen lista. Los nuevos tenants usarán esta versión."
echo ""
echo "  ⚠️  Los tenants existentes NO se actualizan automáticamente."
echo "  Para actualizar un tenant existente:"
echo "    docker compose -f tenants/<slug>/docker-compose.yml pull"
echo "    docker compose -f tenants/<slug>/docker-compose.yml up -d"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
