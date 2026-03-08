#!/usr/bin/env bash
# setup-dnsmasq-local.sh
# Configura dnsmasq via NetworkManager para resolver *.local.test a la IP LAN
# de esta máquina. Así todos los dispositivos de la misma WiFi pueden acceder
# a los tenants si configuran esta máquina como su servidor DNS.
#
# Uso:
#   bash scripts/setup-dnsmasq-local.sh
#
# Para deshacer:
#   sudo rm /etc/NetworkManager/conf.d/dnsmasq.conf
#   sudo rm /etc/NetworkManager/dnsmasq.d/local-test.conf
#   sudo systemctl restart NetworkManager
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# Detectar IP LAN automáticamente (la IP de la interfaz por defecto)
LAN_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')

if [ -z "$LAN_IP" ]; then
    echo "ERROR: No se pudo detectar la IP LAN."
    exit 1
fi

echo "IP LAN detectada: $LAN_IP"
echo "El dominio *.local.test resolverá a $LAN_IP"
echo ""

# 1 — Activar plugin dnsmasq en NetworkManager
sudo tee /etc/NetworkManager/conf.d/dnsmasq.conf > /dev/null << 'EOF'
[main]
dns=dnsmasq
EOF

# 2 — Regla wildcard + escuchar en LAN y loopback
sudo mkdir -p /etc/NetworkManager/dnsmasq.d
sudo tee /etc/NetworkManager/dnsmasq.d/local-test.conf > /dev/null << EOF
# Resolucion wildcard: *.local.test → IP LAN de esta maquina
address=/.local.test/$LAN_IP
# Escuchar tambien en la IP LAN para que otros dispositivos puedan usar
# esta maquina como servidor DNS
listen-address=$LAN_IP
listen-address=127.0.0.1
EOF

# 3 — Reiniciar NetworkManager para aplicar cambios
echo "Reiniciando NetworkManager..."
sudo systemctl restart NetworkManager
sleep 2

# 4 — Verificar
echo ""
echo "Verificando resolución..."
if host meta.local.test 127.0.0.1 2>/dev/null | grep -q "$LAN_IP"; then
    echo "✓ meta.local.test → $LAN_IP (OK)"
else
    echo "? Verificación fallida — puede que NetworkManager tarde unos segundos"
    echo "  Prueba: host meta.local.test 127.0.0.1"
fi

echo ""
echo "=== Para que dispositivos Android accedan ==="
echo "En el router WiFi, configura la IP DNS primaria como: $LAN_IP"
echo "O en cada Android: Ajustes WiFi → IP estática → DNS1: $LAN_IP"
echo ""
echo "Recuerda que Traefik debe escuchar en 0.0.0.0:80 (ya está así en el compose)."
