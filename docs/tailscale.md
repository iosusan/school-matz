# Configuración de Tailscale

Tailscale permite acceder al sistema desde **fuera de la red del aula** (casa, otro centro, móvil con datos) sin abrir puertos en el router.

## Instalación en el servidor (Ubuntu)

```bash
# 1. Instalar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Autenticar el servidor con tu cuenta Tailscale
sudo tailscale up

# 3. Ver la IP de Tailscale asignada al servidor
tailscale ip -4
# Ejemplo: 100.64.0.5
```

## Instalación en el móvil

1. Instalar **Tailscale** desde App Store o Google Play
2. Iniciar sesión con la misma cuenta que el servidor
3. El móvil ya puede acceder al servidor por su IP Tailscale

## Acceso desde fuera del aula

Una vez conectados ambos dispositivos a Tailscale, acceder vía:

```
https://100.64.0.X/
```

> La IP Tailscale es fija y no cambia aunque el servidor cambie de red.

## Nombre de host con Tailscale (MagicDNS)

Tailscale incluye **MagicDNS**: si lo activas en la consola de Tailscale, el servidor es accesible por su hostname directamente:

```
https://materiales/
```

Para activarlo: https://login.tailscale.com/admin/dns → activar MagicDNS

## Nota sobre el certificado SSL

Con Tailscale + certificado autofirmado, el navegador seguirá mostrando la advertencia de seguridad la primera vez. Para evitarlo con Tailscale puedes usar **Tailscale HTTPS certificates** (gratuito):

```bash
# Genera un certificado TLS válido para el dominio Tailscale del servidor
sudo tailscale cert materiales.tu-tailnet.ts.net

# El certificado se guarda en /var/lib/tailscale/certs/
# Actualiza nginx-materiales.conf para usar esos certificados en vez de los autofirmados
```

## Resumen de acceso

| Situación | URL |
|---|---|
| Mismo WiFi del aula | `https://materiales.local` |
| Fuera del aula (con Tailscale) | `https://materiales` (MagicDNS) o `https://100.64.0.X` |
