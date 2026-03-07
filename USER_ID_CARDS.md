# USER_ID_CARDS — Plan de Implementación de Carnets de Usuario con QR

> **Estado:** Planificación
> **Fecha:** Marzo 2026
> **Depende de:** Fase 2 completada

---

## 1. Objetivo

Añadir un sistema de identificación por QR personal para cada usuario, que funcione
en **paralelo** a la selección de nombre existente. El usuario decide en cada momento
qué método usa. Los carnets se generan como PDF en formato de **carnet de biblioteca**
(nombre + código QR en lugar de foto) y se pueden imprimir para que cada alumno/profesor
lleve el suyo.

---

## 2. Comportamiento Esperado

### Flujo de identificación actual (sigue funcionando igual)
```
SACAR MATERIAL → Seleccionar nombre de la lista → Escanear QR del objeto
```

### Flujo nuevo (alternativo)
```
SACAR MATERIAL → Escanear carnet QR de usuario → Escanear QR del objeto
```

### Selección del método en el móvil
En la pantalla de inicio del flujo "Sacar material", se presenta una elección:

```
┌─────────────────────────────┐
│  ← Sacar Material           │
│                             │
│  ¿Cómo te identificas?      │
│                             │
│  ┌─────────────────────┐    │
│  │  👤 Seleccionar     │    │
│  │     mi nombre       │    │
│  └─────────────────────┘    │
│                             │
│  ┌─────────────────────┐    │
│  │  🪪 Escanear        │    │
│  │     mi carnet       │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

La preferencia se recuerda con `localStorage` para no preguntar cada vez.

---

## 3. Cambios Necesarios

### 3.1 Base de datos — Modelo `Usuario`

Añadir campo `codigo_qr` único, generado automáticamente al crear el usuario:

```
usuarios
┌──────────────────────────────┐
│ id           INTEGER PK      │
│ nombre       TEXT            │
│ apellido     TEXT            │
│ activo       BOOLEAN         │
│ codigo_qr    TEXT UNIQUE  ←  │  NUEVO  formato: USR-00001
│ created_at   DATETIME        │
└──────────────────────────────┘
```

**Migración:** Para usuarios existentes sin `codigo_qr`, generarlo automáticamente
al arrancar la aplicación si el campo está vacío (lógica en `main.py` o en un script
de migración ad-hoc).

> **Decisión de diseño:** Se usa el mismo patrón que `Material.codigo_qr` para
> consistencia — formato `USR-XXXXX` (5 dígitos con ceros a la izquierda).

### 3.2 Contenido del QR de usuario

El QR codifica la URL completa (paralelo a los QR de material):

```
https://materiales.local/usuario/USR-00001
```

El frontend extrae el código `USR-XXXXX` de la URL mediante regex, igual que hace
con los QR de material.

### 3.3 Backend — Nuevos endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/usuarios/qr/{codigo_qr}` | Buscar usuario por código QR ← **clave para el escáner** |
| GET | `/usuarios/{id}/qr/imagen` | Descargar PNG del QR del usuario |
| GET | `/usuarios/pdf-carnets` | PDF con carnets de todos los usuarios activos |
| GET | `/usuarios/pdf-carnets?ids=1,2,3` | PDF con carnets de usuarios seleccionados |

### 3.4 Backend — Servicio de generación de QR de usuario

Reutiliza `qr_service.py` con adaptaciones:

- Imagen PNG: QR + nombre + apellido + código `USR-XXXXX`
- Los PNG se almacenan en `./static/qr_usuarios/`

### 3.5 Backend — Servicio PDF de carnets (`pdf_carnet_service.py`)

Formato carnet de biblioteca: **85 × 54 mm** (tamaño tarjeta de crédito estándar),
disposición 2 carnets por fila en hoja A4 (2×5 = 10 carnets por página).

Diseño de cada carnet:
```
┌──────────────────────────────────────────┐
│  🏫 Aula de Recursos      USR-00001      │
│ ─────────────────────────────────────── │
│                                          │
│        ┌──────────────┐                  │
│        │              │  García          │
│        │   QR code    │  Ana             │
│        │              │                  │
│        └──────────────┘                  │
│                                          │
└──────────────────────────────────────────┘
```

Elementos:
- **Cabecera:** nombre del sistema + código de usuario (esquina superior derecha)
- **QR:** ocupa ~40% del ancho del carnet, centrado verticalmente
- **Nombre:** apellido en negrita (grande) + nombre debajo, alineados a la derecha del QR
- **Bordes redondeados** simulados con rectángulo con radio

### 3.6 Frontend — Pantalla móvil

**Cambio 1:** Nueva pantalla de elección de método de identificación (entre "Sacar" y la lista de usuarios actual).

**Cambio 2:** Nueva pantalla de escáner de carnet (reutiliza `Html5Qrcode`), extrae `USR-XXXXX` de la URL escaneada, llama a `GET /usuarios/qr/{codigo_qr}`, y si lo encuentra avanza al escáner de material mostrando el nombre del usuario identificado.

**Cambio 3:** `localStorage` guarda el último método usado (`id_method: "list" | "qr"`) para pre-seleccionarlo la próxima vez.

### 3.7 Frontend — Panel de administración (`admin.html`)

**Tab Usuarios:**
- Nueva columna `Código` con el `USR-XXXXX`
- Botón `QR` por fila (descarga PNG individual, igual que en material)
- Botón global `🪪 PDF carnets` (descarga todos los activos)

---

## 4. Plan de Implementación por Pasos

### Paso 1 — Modelo y migración
- [ ] Añadir `codigo_qr: str` al modelo `Usuario` (`UNIQUE`, `nullable=True` inicialmente)
- [ ] Actualizar schema `UsuarioOut` para incluir `codigo_qr`
- [ ] En `main.py` al arrancar: asignar `USR-XXXXX` a usuarios que no tengan código
- [ ] Asignar código en `crear_usuario()` como en `crear_material()`

### Paso 2 — QR service para usuarios
- [ ] Añadir función `generate_qr_usuario(codigo_qr, nombre, apellido)` en `qr_service.py`
  - URL: `https://materiales.local/usuario/{codigo_qr}`
  - PNG con QR + nombre completo + código
  - Guardado en `./static/qr_usuarios/`
- [ ] Llamar a esta función en `crear_usuario()` y en `actualizar_usuario()`

### Paso 3 — Endpoints backend
- [ ] `GET /usuarios/qr/{codigo_qr}` → devuelve `UsuarioOut` ó 404
- [ ] `GET /usuarios/{id}/qr/imagen` → `FileResponse` del PNG
- [ ] `GET /usuarios/pdf-carnets` con filtro `ids` opcional

### Paso 4 — Servicio PDF carnets
- [ ] Crear `backend/services/pdf_carnet_service.py`
- [ ] Tamaño tarjeta (85×54 mm), 2 columnas × 5 filas por página A4
- [ ] Diseño: cabecera con nombre del sistema, QR, nombre/apellido

### Paso 5 — Frontend móvil
- [ ] Nueva pantalla `metodo-identificacion` entre "inicio" e "identificador de usuario"
- [ ] Pantalla `scanner-usuario`: igual que `scanner` pero activa al leer `USR-XXXXX`
- [ ] Lógica de detección: regex `/USR-\d{5}/` sobre la URL escaneada
- [ ] Guardar preferencia en `localStorage`

### Paso 6 — Panel admin
- [ ] Columna `Código` en tabla de usuarios
- [ ] Enlace `QR` por fila → `GET /usuarios/{id}/qr/imagen`
- [ ] Botón `🪪 PDF carnets` → `GET /usuarios/pdf-carnets`
- [ ] Selector de usuarios para carnets parciales (checkboxes, igual que material)

### Paso 7 — Ruta `/usuario/:codigo_qr` en el frontend
- [ ] El QR del carnet apunta a `https://materiales.local/usuario/USR-00001`
- [ ] FastAPI debe servir `index.html` para esa ruta (ya lo hace con el catch-all `/`)
- [ ] El JS detecta `window.location.pathname` con patrón `/usuario/USR-XXXXX` al cargar
  y arranca directamente en el flujo "Sacar material" con ese usuario pre-identificado
  (UX extra: escanear el carnet desde fuera de la app también funciona)

---

## 5. Impacto en Código Existente

| Fichero | Tipo de cambio |
|---|---|
| `backend/models/usuario.py` | Añadir campo `codigo_qr` |
| `backend/schemas/usuario.py` | Añadir `codigo_qr` a `UsuarioOut` |
| `backend/routers/usuarios.py` | 3 nuevos endpoints + asignar QR en crear/actualizar |
| `backend/services/qr_service.py` | Nueva función `generate_qr_usuario()` |
| `backend/services/pdf_carnet_service.py` | Fichero nuevo |
| `backend/main.py` | Migración inline: asignar QR a usuarios sin código al arrancar |
| `frontend/index.html` | Nueva pantalla + lógica de bifurcación |
| `frontend/admin.html` | Columna + botón en tab Usuarios |
| `frontend/js/api.js` | 3 nuevos métodos |

---

## 6. Consideraciones

- **Colisión de escáneres:** la pantalla del escáner de material no debe activarse con
  un QR de usuario (`USR-XXXXX`) ni al revés. Añadir validación en el JS que distinga
  el prefijo `MAT-` vs `USR-`.

- **Regenerar QR:** si se cambia el nombre de un usuario, el QR de identificación
  **no cambia** (el código `USR-XXXXX` es permanente). Solo cambia el PNG decorativo
  que muestra el nombre. Regenerar el PNG en `actualizar_usuario()`.

- **Usuarios sin carnet impreso:** el sistema sigue funcionando con la lista de nombres
  como fallback, sin necesidad de que todos tengan carnet físico.

- **Privacidad:** el carnet no muestra información sensible. Solo nombre + código opaco.
  El código QR no contiene el nombre, solo la URL con el identificador.
