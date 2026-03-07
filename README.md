


# requisitos


# instalacion

0. sudo bash scripts/setup_mkcert.sh
1. sudo bash scripts/setup_avahi.sh
2. sudo bash scripts/setup_nginx.sh
3. sudo cp scripts/school-assets.service /etc/systemd/system/
4. sudo systemctl enable --now school-assets



### antiguo
1. bash scirpts/gen_cert.sh

✅ Certificado generado en /home/iosu/projects/school_matz/scripts/certs/

En el móvil, la primera vez que accedas a https://materiales.local
verás un aviso de seguridad. Pulsa 'Avanzado' → 'Aceptar riesgo y continuar'.

2. sudo bash scripts/setup_avahi.sh

✅ Avahi configurado. El servidor es accesible como 'materiales.local'
   Verifica con: avahi-resolve -n materiales.local

( instalar nginx en el sistema si no lo tienes: sudo apt install nginx )
3. sudo bash scripts/setup_nginx.sh

✅ Nginx configurado.
   https://materiales.local → proxy a FastAPI en puerto 8000


4. sudo cp scripts/nginx-materiales.conf /etc/nginx/sites-available/materiales

5. sudo nginx -t && sudo systemctl reload nginx
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

6. sudo cp scripts/school-assets.service /etc/systemd/system/

7. sudo systemctl enable --now school-assets

--- esto pone sl servicio en marcha en el puerto 8000 local
y añade 'materiales.local' en la wifi ----


################

# Instalación del servidor

1. **Certificado SSL con mkcert** (sin advertencias en el navegador):
   ```bash
   sudo bash scripts/setup_mkcert.sh
   ```
   Esto instala mkcert, crea la CA local y genera `certs/materiales.crt`.

   *Alternativa rápida sin mkcert (con advertencia en el navegador):*
   ```bash
   bash scripts/gen_cert.sh
   ```

2. **Avahi mDNS** (para que `materiales.local` sea accesible en la red):
   ```bash
   sudo bash scripts/setup_avahi.sh
   # Verificar con:
   avahi-resolve -n materiales.local
   ```

3. **Nginx** (proxy HTTPS en el puerto 443):
   ```bash
   sudo bash scripts/setup_nginx.sh
   ```

4. **Servicio systemd**:
   ```bash
   sudo cp scripts/school-assets.service /etc/systemd/system/
   sudo systemctl enable --now school-assets
   ```

---

## Instalar el certificado raíz en cada dispositivo

Para que el navegador no muestre advertencias de seguridad, hay que instalar
el root CA **una sola vez** en cada dispositivo que acceda al sistema.

Descarga directa desde cualquier dispositivo en la misma WiFi:
```
http://materiales.local/rootCA.pem
```

### iOS / iPadOS
1. En **Safari**, abre `http://materiales.local/rootCA.pem` (se descarga automáticamente)
2. **Ajustes → General → VPN y gestión del dispositivo → Instalar perfil**
3. **Ajustes → General → Información → Confianza de certificados** →
   activa `mkcert root@materiales` como certificado raíz de confianza completa

### Android
> ⚠️ Chrome en Android 7+ **no confía en CAs de usuario** para HTTPS.
> Usar **Firefox para Android** es la opción más sencilla.

**Con Firefox para Android:**
1. Descarga `http://materiales.local/rootCA.pem`
2. Instala el certificado en Ajustes del sistema →
   Seguridad → Credenciales de confianza → Instalar CA
3. Firefox → `about:config` →
   `security.enterprise_roots.enabled` → `true`

### Windows / macOS (portátil del profesor)
```bash
CAROOT=/home/iosu/projects/school_matz/certs/ca mkcert -install
```
O bien, doble clic en `rootCA.pem` → Instalar en "Entidades de certificación raíz de confianza".

---
