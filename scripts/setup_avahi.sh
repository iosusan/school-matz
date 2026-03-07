#!/usr/bin/env bash
# Configura Avahi para que este servidor se anuncie en la red local
# como "materiales.local" (mDNS).
#
# Ejecutar una sola vez con: sudo bash scripts/setup_avahi.sh

set -e

echo "→ Instalando avahi-daemon si no está presente…"
apt-get install -y avahi-daemon avahi-utils

echo "→ Configurando hostname del sistema como 'materiales'…"
hostnamectl set-hostname materiales

# Actualizar /etc/hosts para evitar resolución lenta
if ! grep -q "127.0.1.1.*materiales" /etc/hosts; then
  sed -i "s/^127.0.1.1.*/127.0.1.1\tmateriales materiales.local/" /etc/hosts
fi

echo "→ Detectando interfaz de red activa…"
IFACE=$(ip -br link show | awk '$2 == "UP" && $1 != "lo" && $1 !~ /^(docker|br-|veth)/ {print $1; exit}')
echo "   Interfaz detectada: $IFACE"

echo "→ Configurando avahi-daemon…"
cat > /etc/avahi/avahi-daemon.conf << EOF
[server]
host-name=materiales
domain-name=local
use-ipv4=yes
use-ipv6=no
allow-interfaces=$IFACE
deny-interfaces=lo
ratelimit-interval-usec=1000000
ratelimit-burst=1000

[wide-area]
enable-wide-area=no

[publish]
publish-addresses=yes
publish-hinfo=yes
publish-workstation=yes
publish-domain=yes
EOF


echo "→ Corrigiendo /etc/nsswitch.conf para que mdns tenga prioridad sobre dns…"
sed -i.bak 's/^hosts:.*/hosts:          files mdns4_minimal [NOTFOUND=return] dns/' /etc/nsswitch.conf
grep ^hosts /etc/nsswitch.conf

echo "→ Activando y arrancando avahi-daemon…"
systemctl enable avahi-daemon
systemctl restart avahi-daemon

echo ""
echo "✅ Avahi configurado. El servidor es accesible como 'materiales.local'"
echo "   Verifica con: avahi-resolve -n materiales.local"
