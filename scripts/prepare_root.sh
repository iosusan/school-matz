#!/usr/bin/env bash
# prepare_root.sh — Creación interactiva del superadministrador.
# Ejecutar tras el primer arranque (cuando la BD ya existe).
#
# Uso: bash scripts/prepare_root.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Localizar Python del venv
if [[ -f "$SCRIPT_DIR/.venv/bin/python" ]]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
  PYTHON="python3"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔐 Configuración del superadministrador"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar si ya existe algún superadmin
EXISTING=$(ADMIN_USER=__check__ ADMIN_PASS=__check__ "$PYTHON" -c "
import sys, os
sys.path.insert(0, '.')
from backend.database import Base, engine
from backend.models.admin_user import AdminUser
from sqlalchemy.orm import Session
Base.metadata.create_all(bind=engine)
with Session(engine) as db:
    n = db.query(AdminUser).filter(AdminUser.is_superadmin == True).count()
    print(n)
" 2>/dev/null || echo "0")

if [[ "$EXISTING" -gt 0 ]]; then
  echo "  ⚠️  Ya existe un superadministrador configurado."
  echo -n "  ¿Deseas crear uno nuevo o cambiar la contraseña del existente? [s/N]: "
  read -r CONFIRM
  if [[ "${CONFIRM,,}" != "s" ]]; then
    echo "  Cancelado."
    exit 0
  fi
fi

# Pedir nombre de usuario
echo -n "  Nombre de usuario: "
read -r ADMIN_USER
if [[ -z "$ADMIN_USER" ]]; then
  echo "  ❌ El nombre de usuario no puede estar vacío."
  exit 1
fi

# Pedir contraseña (oculta, con confirmación)
while true; do
  echo -n "  Contraseña (mínimo 8 caracteres): "
  read -rs ADMIN_PASS
  echo ""
  if [[ ${#ADMIN_PASS} -lt 8 ]]; then
    echo "  ❌ Debe tener al menos 8 caracteres."
    continue
  fi
  echo -n "  Confirmar contraseña: "
  read -rs ADMIN_PASS2
  echo ""
  if [[ "$ADMIN_PASS" != "$ADMIN_PASS2" ]]; then
    echo "  ❌ Las contraseñas no coinciden."
    continue
  fi
  break
done

# Crear/actualizar superadmin (credenciales via env, nunca como argumento)
ADMIN_USER="$ADMIN_USER" ADMIN_PASS="$ADMIN_PASS" "$PYTHON" scripts/create_superadmin.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Superadmin listo. Accede a la app y usa estas"
echo "     credenciales en el panel de administración."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
