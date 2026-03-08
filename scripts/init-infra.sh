#!/usr/bin/env bash
# scripts/init-infra.sh — Inicialización de infraestructura multitenant.
# Ejecutar UNA VEZ en el servidor antes del primer despliegue.
#
# Uso: bash scripts/init-infra.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🐳 School-Matz — Inicialización de infraestructura"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Red Docker externa compartida ─────────────────────────────────────────
if docker network inspect traefik_public >/dev/null 2>&1; then
  echo "  ✅ Red 'traefik_public' ya existe."
else
  docker network create traefik_public
  echo "  ✅ Red 'traefik_public' creada."
fi

# ── 2. Fichero de certificados Let's Encrypt ──────────────────────────────────
ACME_FILE="$SCRIPT_DIR/traefik/acme.json"
mkdir -p "$SCRIPT_DIR/traefik"
if [[ ! -f "$ACME_FILE" ]]; then
  touch "$ACME_FILE"
  echo "  ✅ Fichero acme.json creado."
else
  echo "  ✅ Fichero acme.json ya existe."
fi
# Traefik exige permisos 600 en acme.json
chmod 600 "$ACME_FILE"
echo "  ✅ Permisos de acme.json: 600."

# ── 3. Directorio de tenants ──────────────────────────────────────────────────
mkdir -p "$SCRIPT_DIR/tenants"
echo "  ✅ Directorio tenants/ listo."

# ── 4. Resumen ────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Infraestructura lista. Próximos pasos:"
echo ""
echo "  1. Edita traefik/traefik.yml y pon tu email real en acme.email"
echo "  2. Levanta Traefik:"
echo "       docker compose -f docker-compose.infra.yml up -d"
echo "  3. Levanta la app (tenant manual / modo legacy):"
echo "       docker compose up -d"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
