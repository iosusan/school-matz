#!/bin/sh
# avahi-watcher.sh — Vigila /etc/avahi/hosts y recarga avahi-daemon cuando cambia.
# Corre dentro de un contenedor Alpine con pid:host y privileged:true.
# Requiere que el archivo /etc/avahi/hosts y /run/avahi-daemon/ estén montados.

echo "Avahi watcher iniciado (polling cada 2s)"

LAST=""
while true; do
    CURR=$(md5sum /etc/avahi/hosts 2>/dev/null)
    if [ "$CURR" != "$LAST" ]; then
        LAST="$CURR"
        PID=$(cat /run/avahi-daemon/pid 2>/dev/null)
        if [ -n "$PID" ]; then
            kill -HUP "$PID" 2>/dev/null && echo "avahi-daemon recargado ($(date))"
        else
            echo "avahi-daemon no encontrado — /run/avahi-daemon/pid no existe"
        fi
    fi
    sleep 2
done
