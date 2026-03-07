# SCHOOL_ASSET_MGMT — Plan Detallado del Sistema de Gestión de Material de Aula

> **Versión:** 2.0  
> **Fecha:** Marzo 2026  
> **Estado:** Fase 2 completada — Fase 3 en curso

---

## Índice

1. [Visión General](#1-visión-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Modelo de Base de Datos](#4-modelo-de-base-de-datos)
5. [API REST — Endpoints](#5-api-rest--endpoints)
6. [Sistema de Códigos QR](#6-sistema-de-códigos-qr)
7. [Interfaz de Usuario](#7-interfaz-de-usuario)
8. [Flujos de Uso Detallados](#8-flujos-de-uso-detallados)
9. [Estructura de Ficheros del Proyecto](#9-estructura-de-ficheros-del-proyecto)
10. [Plan de Desarrollo por Fases](#10-plan-de-desarrollo-por-fases)
11. [Instalación y Despliegue](#11-instalación-y-despliegue)
12. [Requisitos de Hardware](#12-requisitos-de-hardware)
13. [Seguridad y Backups](#13-seguridad-y-backups)
14. [Mejoras Futuras](#14-mejoras-futuras)
15. [Despliegue en Cloud (AWS)](#15-despliegue-en-cloud-aws)

---

## 1. Visión General

### Objetivo
Sistema para gestionar el material de un aula escolar: registrar préstamos y devoluciones de objetos físicos mediante lectura de códigos QR desde un teléfono móvil, con una base de datos centralizada que almacena todo el historial.

### Principios de Diseño
- **Máxima simplicidad:** mínimo de pasos para registrar una operación
- **Sin dependencia de internet:** funciona completamente en red local
- **Sin app nativa:** el móvil usa el navegador web, sin instalaciones
- **Un solo punto de datos:** base de datos única en el servidor local
- **Bajo coste de mantenimiento:** tecnologías ampliamente conocidas

### Escenario Típico de Uso
```
Alumno/Profesor coge material
    └─→ Abre navegador en el móvil
    └─→ Selecciona su nombre
    └─→ Escanea el QR del objeto con la cámara
    └─→ Sistema registra la salida

Alumno/Profesor devuelve material
    └─→ Abre navegador en el móvil
    └─→ Escanea el QR del objeto
    └─→ Sistema detecta quién lo tiene y registra la entrada
```

---

## 2. Arquitectura del Sistema

### Diagrama General

```
┌─────────────────────────────────────────────────────────────┐
│                        RED LOCAL (WiFi)                      │
│                                                             │
│   ┌──────────────┐              ┌─────────────────────────┐ │
│   │   MÓVIL      │◄────HTTP────►│   MINIPC / PORTÁTIL     │ │
│   │              │              │                         │ │
│   │ 📷 Cámara QR │              │  ┌───────────────────┐  │ │
│   │ 🌐 Navegador │              │  │  FastAPI (Python) │  │ │
│   │              │              │  │  Puerto 8000      │  │ │
│   └──────────────┘              │  └────────┬──────────┘  │ │
│                                 │           │              │ │
│   ┌──────────────┐              │  ┌────────▼──────────┐  │ │
│   │  PORTÁTIL /  │◄────HTTP────►│  │   SQLite DB       │  │ │
│   │  ADMIN       │              │  │   assets.db       │  │ │
│   │              │              │  └───────────────────┘  │ │
│   └──────────────┘              └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Ubicación | Responsabilidad |
|---|---|---|
| **FastAPI Server** | MiniPC/Portátil | Sirve la API REST y los ficheros estáticos del frontend |
| **SQLite Database** | MiniPC/Portátil | Almacena todos los datos en un único fichero `.db` |
| **Frontend Web** | Servido por FastAPI | Interfaz de usuario para móvil y administración |
| **Escáner QR** | Móvil (navegador) | Lee QRs usando la cámara mediante librería JS |
| **Generador QR** | MiniPC/Portátil | Genera imágenes QR para imprimir (Python) |

### ¿Por qué esta arquitectura?

- **SQLite** no requiere instalar ni configurar un servidor de base de datos. Todo es un fichero que se puede copiar como backup.
- **FastAPI** sirve tanto la API como el HTML/JS estático, por lo que solo hay un proceso corriendo.
- **El móvil no necesita app** porque los navegadores modernos permiten acceder a la cámara mediante HTTPS (se usará un certificado autofirmado en red local).

---

## 3. Stack Tecnológico

### Backend

| Tecnología | Versión real | Uso |
|---|---|---|
| Python | 3.10.12 | Lenguaje principal del servidor |
| FastAPI | 0.135.1 | Framework web para la API REST |
| SQLite | 3.x (incluido en Python) | Base de datos |
| SQLAlchemy | 2.0.48 | ORM para interactuar con SQLite |
| ~~Alembic~~ | — | **No usado** — tablas creadas con `Base.metadata.create_all()` al arrancar |
| qrcode[pil] | 8.2 | Generación de imágenes QR |
| Pillow | 12.1.1 | Procesamiento de imágenes para QR |
| reportlab | 4.4.10 | Generación de PDF de etiquetas |
| Uvicorn | 0.41.0 | Servidor ASGI para FastAPI |
| pydantic-settings | 2.13.1 | Configuración por variables de entorno |

> **Decisión:** Se descartó Alembic para simplificar el despliegue. Al ser DB de cero, `create_all` es suficiente. Si en el futuro se necesitan migraciones se puede añadir Alembic sin cambiar el modelo.

### Frontend

| Tecnología | Versión | Uso |
|---|---|---|
| HTML5 + CSS3 | — | Estructura y estilos base |
| JavaScript (Vanilla) | ES2022 | Lógica de la interfaz |
| html5-qrcode | 2.3.x | Escáner QR en el navegador (vía CDN) |
| TailwindCSS | 3.x (CDN) | Estilos utilitarios sin compilación |

### Herramientas de Desarrollo

| Herramienta | Uso |
|---|---|
| Git | Control de versiones |
| Poetry 2.3.2 | Gestión de dependencias y entorno virtual (`.venv/` en raíz del proyecto) |
| pytest | Tests del backend (Fase 3) |
| mkcert 1.4.4 | Generación de certificados SSL firmados por CA local |

> **Decisión:** Se usa **Poetry** en lugar de pip+requirements.txt para gestión de dependencias reproducible.

---

## 4. Modelo de Base de Datos

### Diagrama Entidad-Relación

```
categorias
┌─────────────────────────┐
│ id            INTEGER PK│
│ nombre        TEXT      │◄──────────────────┐
│ descripcion   TEXT      │                   │ (auto-referencia)
│ padre_id      INTEGER FK├───────────────────┘
│ created_at    DATETIME  │
└──────────┬──────────────┘
           │ 1
           │
           │ N
usuarios                       material
┌─────────────────────────┐    ┌───────────────────────────┐
│ id            INTEGER PK│    │ id            INTEGER PK  │
│ nombre        TEXT      │    │ codigo_qr     TEXT UNIQUE │
│ apellido      TEXT      │    │ descripcion   TEXT        │
│ activo        BOOLEAN   │    │ categoria_id  INTEGER FK──┤→ categorias
│ created_at    DATETIME  │    │ estado        TEXT        │
└──────────┬──────────────┘    │ notas         TEXT        │
           │ 1                 │ created_at    DATETIME    │
           │                   └──────────┬────────────────┘
           │ N                            │ 1
           │                              │ N
           └──────────┐     ┌─────────────┘
                      │     │
                   movimientos
              ┌──────────────────────────────┐
              │ id            INTEGER PK     │
              │ material_id   INTEGER FK─────┤→ material
              │ usuario_id    INTEGER FK─────┤→ usuarios
              │ tipo          TEXT           │  ('salida' | 'entrada')
              │ fecha_hora    DATETIME       │
              │ notas         TEXT           │
              └──────────────────────────────┘
```

### Definición SQL Completa

```sql
-- Tabla de categorías (árbol jerárquico, sin límite de niveles)
CREATE TABLE categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT,
    padre_id    INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    apellido    TEXT NOT NULL,
    activo      BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de material
CREATE TABLE material (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_qr    TEXT NOT NULL UNIQUE,  -- ej: "MAT-00042"
    descripcion  TEXT NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    estado       TEXT DEFAULT 'disponible'
                 CHECK(estado IN ('disponible', 'prestado', 'baja')),
    notas        TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de movimientos (historial completo)
CREATE TABLE movimientos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL REFERENCES material(id),
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    tipo        TEXT NOT NULL CHECK(tipo IN ('salida', 'entrada')),
    fecha_hora  DATETIME DEFAULT CURRENT_TIMESTAMP,
    notas       TEXT
);

-- Índices para consultas frecuentes
CREATE INDEX idx_movimientos_material ON movimientos(material_id);
CREATE INDEX idx_movimientos_usuario  ON movimientos(usuario_id);
CREATE INDEX idx_movimientos_fecha    ON movimientos(fecha_hora);
CREATE INDEX idx_material_estado      ON material(estado);
CREATE INDEX idx_material_qr          ON material(codigo_qr);
```

### Notas sobre el Modelo

- **Ontología de categorías:** el campo `padre_id` auto-referenciado permite un árbol de profundidad ilimitada. Ejemplo:
  ```
  Deportes
    └── Balones
          ├── Fútbol
          └── Baloncesto
    └── Raquetas
  Informática
    └── Cables
    └── Periféricos
  ```
- **Estado del material:** el campo `estado` en la tabla `material` es redundante con el historial pero permite consultas rápidas de inventario sin recorrer `movimientos`.
- **codigo_qr:** se genera automáticamente en el servidor con el formato `MAT-XXXXX` (5 dígitos con ceros a la izquierda). Este código se incrusta en la imagen QR.

---

## 5. API REST — Endpoints

### Base URL
```
http://<IP_SERVIDOR>:8000/api/v1
```

### Usuarios

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/usuarios` | Listar todos los usuarios activos |
| GET | `/usuarios/{id}` | Obtener un usuario por ID |
| POST | `/usuarios` | Crear nuevo usuario |
| PUT | `/usuarios/{id}` | Modificar usuario |
| DELETE | `/usuarios/{id}` | Desactivar usuario (soft delete) |

### Categorías

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/categorias` | Listar árbol completo de categorías |
| GET | `/categorias/{id}` | Obtener categoría con sus hijos |
| POST | `/categorias` | Crear nueva categoría |
| PUT | `/categorias/{id}` | Modificar categoría |
| DELETE | `/categorias/{id}` | Eliminar categoría (si no tiene material) |

### Material

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/material` | Listar todo el material (con filtros opcionales) |
| GET | `/material/{id}` | Obtener material por ID |
| GET | `/material/qr/{codigo_qr}` | Buscar material por código QR ← **clave para el escáner** |
| POST | `/material` | Crear nuevo material (genera código QR automáticamente) |
| PUT | `/material/{id}` | Modificar material |
| DELETE | `/material/{id}` | Dar de baja material |
| GET | `/material/{id}/qr/imagen` | Descargar imagen PNG del QR |
| GET | `/material/qr/lote` | Generar PDF con QRs de varios materiales para imprimir |

### Movimientos

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/movimientos` | Listar movimientos (con filtros: usuario, material, fecha, tipo) |
| POST | `/movimientos/salida` | Registrar salida de material |
| POST | `/movimientos/entrada` | Registrar entrada (devolución) de material |
| GET | `/movimientos/activos` | Listar material actualmente prestado |
| GET | `/material/{id}/historial` | Historial completo de un objeto |
| GET | `/usuarios/{id}/historial` | Historial de préstamos de un usuario |

### Ejemplos de Payload

**Registrar salida:**
```json
POST /api/v1/movimientos/salida
{
  "codigo_qr": "MAT-00042",
  "usuario_id": 7,
  "notas": "Clase de educación física"
}
```

**Respuesta:**
```json
{
  "ok": true,
  "movimiento_id": 128,
  "material": {
    "id": 42,
    "descripcion": "Balón de fútbol",
    "codigo_qr": "MAT-00042"
  },
  "usuario": {
    "nombre": "Ana",
    "apellido": "García"
  },
  "fecha_hora": "2026-03-07T10:32:11"
}
```

**Registrar entrada (devolución):**
```json
POST /api/v1/movimientos/entrada
{
  "codigo_qr": "MAT-00042"
}
```
> La entrada no requiere usuario porque el sistema sabe quién lo tiene por el último movimiento de tipo `salida`.

---

## 6. Sistema de Códigos QR

### Generación de Códigos

Los códigos QR se generan en el servidor con Python usando la librería `qrcode`. El contenido del QR es la **URL completa** del material:

```
https://materiales.local/scan/MAT-00042
```

> **Decisión:** Se optó por la URL completa (Opción B) en lugar del código corto, para que cualquier lector QR genérico abra directamente la app sin configuración adicional.

```
┌─────────────────────────┐
│  ▓▓▓ ▓ ▓▓▓ ▓ ▓▓▓       │
│  ▓   ▓   ▓ ▓   ▓       │
│  ▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓       │
│                         │
│       MAT-00042         │
│  Balón de fútbol        │
│  Deportes > Balones     │
└─────────────────────────┘
   Etiqueta imprimible
```

### Formatos de Salida

| Formato | Uso | Endpoint |
|---|---|---|
| PNG individual | Previsualización en pantalla | `GET /material/{id}/qr/imagen` |
| PDF de etiquetas | Impresión de varias etiquetas a la vez | `GET /material/pdf-etiquetas?ids=1,2,3` |

### Diseño de la Etiqueta QR

Cada etiqueta imprimible incluye:
- Imagen QR (código del material)
- Código legible en texto (ej: `MAT-00042`)
- Descripción corta del material
- Categoría

Tamaño recomendado de etiqueta: **4 × 4 cm** (compatible con etiquetas adhesivas estándar tipo Avery).

### Lectura QR en el Móvil

Se usa la librería JavaScript `html5-qrcode` que accede a la cámara trasera del móvil directamente desde el navegador. No requiere instalación de ninguna app. Requiere que el servidor use HTTPS (se configura un certificado autofirmado en red local).

---

## 7. Interfaz de Usuario

### Vista Móvil — Operativa Diaria

#### Pantalla 1: Inicio Operativo
```
┌─────────────────────────┐
│    🏫 Aula de Recursos  │
│                         │
│  ┌───────────────────┐  │
│  │  📤 SACAR         │  │
│  │     MATERIAL      │  │
│  └───────────────────┘  │
│                         │
│  ┌───────────────────┐  │
│  │  📥 DEVOLVER      │  │
│  │     MATERIAL      │  │
│  └───────────────────┘  │
│                         │
│  ┌───────────────────┐  │
│  │  📋 QUÉ HAY       │  │
│  │     PRESTADO      │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

#### Pantalla 2a: Seleccionar Usuario (solo en SACAR)
```
┌─────────────────────────┐
│  ← Sacar Material       │
│                         │
│  ¿Quién eres?           │
│  ┌───────────────────┐  │
│  │ 🔍 Buscar...      │  │
│  └───────────────────┘  │
│                         │
│  García, Ana            │
│  López, Carlos          │
│  Martínez, Lucía        │
│  Pérez, David           │
│  ...                    │
└─────────────────────────┘
```

#### Pantalla 2b: Escáner QR
```
┌─────────────────────────┐
│  ← Escanear objeto      │
│                         │
│  ┌─────────────────┐    │
│  │                 │    │
│  │   [CÁMARA       │    │
│  │    ACTIVA]      │    │
│  │                 │    │
│  └─────────────────┘    │
│                         │
│  Apunta al código QR    │
│  del objeto             │
└─────────────────────────┘
```

#### Pantalla 3: Confirmación
```
┌─────────────────────────┐
│        ✅               │
│   SALIDA REGISTRADA     │
│                         │
│  Objeto:                │
│  🏐 Balón de fútbol     │
│  (MAT-00042)            │
│                         │
│  Prestado a:            │
│  👤 Ana García          │
│                         │
│  10:32 · 7 mar 2026     │
│                         │
│  [  ESCANEAR OTRO  ]    │
│  [     INICIO      ]    │
└─────────────────────────┘
```

### Vista Escritorio — Panel de Administración

#### Sección: Inventario
- Tabla con todos los materiales
- Filtros por: categoría, estado (disponible/prestado/baja), texto libre
- Columnas: código QR, descripción, categoría, estado, último movimiento
- Acciones: editar, dar de baja, descargar QR, ver historial

#### Sección: Usuarios
- Lista de usuarios activos/inactivos
- CRUD completo (nombre, apellido, estado activo)
- Ver historial de préstamos por usuario

#### Sección: Categorías
- Vista de árbol expandible/colapsable
- Crear/editar/eliminar categorías
- Arrastrar para reorganizar jerarquía (drag & drop)

#### Sección: Movimientos
- Tabla cronológica de todos los movimientos
- Filtros: rango de fechas, usuario, material, tipo (entrada/salida)
- Exportar a CSV

#### Sección: Préstamos Activos
- Lista de material actualmente prestado
- Columnas: objeto, prestado a, desde cuándo
- Alerta visual para préstamos de más de X días

#### Sección: Generar QRs
- Seleccionar uno o varios materiales
- Vista previa de etiquetas
- Descargar PDF listo para imprimir

---

## 8. Flujos de Uso Detallados

### Flujo 1: Sacar Material

```
[Usuario en móvil]
       │
       ▼
  Abre navegador → http://192.168.1.50:8000
       │
       ▼
  Pulsa "SACAR MATERIAL"
       │
       ▼
  Selecciona su nombre de la lista
       │ GET /api/v1/usuarios
       ▼
  Apunta la cámara al QR del objeto
       │ (html5-qrcode detecta "MAT-00042")
       ▼
  Frontend llama a la API
       │ GET /api/v1/material/qr/MAT-00042
       ▼
  API verifica estado del objeto
       ├── Si estado = 'prestado' → Error: "Ya está prestado por [nombre]"
       └── Si estado = 'disponible' → Continúa
       │
       ▼
  POST /api/v1/movimientos/salida
  { codigo_qr: "MAT-00042", usuario_id: 7 }
       │
       ▼
  API actualiza material.estado = 'prestado'
  API inserta movimiento tipo='salida'
       │
       ▼
  Frontend muestra pantalla de confirmación ✅
```

### Flujo 2: Devolver Material

```
[Usuario en móvil]
       │
       ▼
  Pulsa "DEVOLVER MATERIAL"
       │
       ▼
  Apunta la cámara al QR del objeto
       │ (html5-qrcode detecta "MAT-00042")
       ▼
  GET /api/v1/material/qr/MAT-00042
       │
       ▼
  API busca último movimiento tipo='salida' para ese objeto
       ├── Si estado = 'disponible' → Error: "Este objeto no está prestado"
       └── Si estado = 'prestado' → Continúa
       │
       ▼
  POST /api/v1/movimientos/entrada
  { codigo_qr: "MAT-00042" }
       │
       ▼
  API actualiza material.estado = 'disponible'
  API inserta movimiento tipo='entrada' con mismo usuario_id
       │
       ▼
  Frontend muestra: "✅ Devuelto — Era de Ana García" 
```

### Flujo 3: Añadir Nuevo Material con QR

```
[Admin en portátil]
       │
       ▼
  Panel Admin → "Nuevo Material"
       │
       ▼
  Rellena formulario:
    - Descripción: "Balón de baloncesto"
    - Categoría: Deportes > Balones > Baloncesto
    - Notas: (opcional)
       │
       ▼
  POST /api/v1/material
  { descripcion: "...", categoria_id: 5 }
       │
       ▼
  API genera código: MAT-00043 (autoincremental)
  API genera imagen QR PNG
  API guarda en base de datos
       │
       ▼
  Frontend muestra QR generado + botón "Imprimir etiqueta"
       │
       ▼
  GET /api/v1/material/43/qr/imagen → descarga PNG
  (o añadir al lote para imprimir varios juntos)
```

### Flujo 4: Imprimir Lote de Etiquetas QR

```
[Admin en portátil]
       │
       ▼
  Panel Admin → "Generar QRs"
       │
       ▼
  Selecciona materiales del inventario (checkboxes)
       │
       ▼
  Pulsa "Generar PDF"
       │
       ▼
  GET /api/v1/material/qr/lote?ids=1,5,12,43
       │
       ▼
  API genera PDF con etiquetas en cuadrícula (4×4 cm c/u)
       │
       ▼
  Navegador descarga el PDF → imprimir en papel de etiquetas
```

---

## 9. Estructura de Ficheros del Proyecto

```
school_matz/                     ← raíz del proyecto
│
├── backend/
│   ├── main.py                  # Punto de entrada FastAPI; crea tablas al arrancar
│   ├── config.py                # pydantic-settings; lee .env
│   ├── database.py              # Engine SQLAlchemy, SessionLocal, get_db
│   │
│   ├── models/                  # Modelos SQLAlchemy (tablas)
│   │   ├── __init__.py
│   │   ├── categoria.py
│   │   ├── usuario.py
│   │   ├── material.py
│   │   └── movimiento.py
│   │
│   ├── schemas/                 # Schemas Pydantic v2
│   │   ├── __init__.py
│   │   ├── categoria.py         # CategoriaOut es recursivo (model_rebuild)
│   │   ├── usuario.py
│   │   ├── material.py
│   │   └── movimiento.py
│   │
│   ├── routers/                 # Endpoints agrupados por recurso
│   │   ├── __init__.py
│   │   ├── categorias.py
│   │   ├── usuarios.py
│   │   ├── material.py          # Incluye /pdf-etiquetas y /qr/{codigo}
│   │   └── movimientos.py       # Incluye filtros fecha_desde/fecha_hasta
│   │
│   └── services/                # Lógica de negocio
│       ├── __init__.py
│       ├── qr_service.py        # Genera PNG con QR + texto (fuente DejaVu)
│       ├── pdf_service.py       # Genera PDF A4 cuadrícula 3×N etiquetas
│       └── movimiento_service.py
│
├── frontend/
│   ├── index.html               # SPA móvil (6 pantallas: inicio/usuario/
│   │                            #   scanner/confirm/error/prestados)
│   ├── admin.html               # Panel admin (5 tabs: material/usuarios/
│   │                            #   categorías/prestados/historial)
│   └── js/
│       └── api.js               # Wrapper fetch para todos los endpoints
│
├── data/
│   └── assets.db                # SQLite (creado automáticamente al arrancar)
│
├── static/
│   └── qr/                      # PNG de QR generados (caché)
│
├── certs/
│   ├── materiales.crt           # Certificado SSL (mkcert, válido hasta jun 2028)
│   ├── materiales.key           # Clave privada
│   ├── rootCA.pem               # CA raíz para instalar en dispositivos
│   └── ca/                      # Directorio CAROOT de mkcert
│
├── scripts/
│   ├── setup_mkcert.sh          # Instala mkcert y genera cert + CA
│   ├── setup_avahi.sh           # Configura mDNS (materiales.local)
│   ├── setup_nginx.sh           # Instala nginx y lo configura
│   ├── nginx-materiales.conf    # Config nginx: 80→443, /rootCA.pem en HTTP
│   ├── gen_cert.sh              # Alternativa: cert autofirmado sin mkcert
│   └── school-assets.service   # Unidad systemd
│
├── docs/
│   └── tailscale.md             # Instrucciones acceso remoto con Tailscale
│
├── .env                         # Variables de entorno activas
├── .env.example                 # Plantilla
├── start.sh                     # Arranque en desarrollo (uvicorn --reload)
├── pyproject.toml               # Dependencias Poetry
└── README.md                    # Instalación y guía de uso
```

---

## 10. Plan de Desarrollo por Fases

### Fase 1 — MVP Funcional ✅ *Completada*

**Objetivo:** el sistema es usable para registrar entradas y salidas.

- [x] Crear estructura del proyecto con **Poetry** (`.venv/` en raíz)
- [x] Definir modelos SQLAlchemy; tablas creadas con `create_all` al arrancar
- [x] Endpoint: listar usuarios
- [x] Endpoint: buscar material por código QR
- [x] Endpoint: registrar salida de material
- [x] Endpoint: registrar entrada de material
- [x] Frontend móvil: flujo completo sacar/devolver con escáner QR
- [x] Configurar HTTPS con certificado autofirmado (`scripts/gen_cert.sh`)
- [x] Script de inicio en desarrollo (`start.sh`)
- [x] Servicio systemd (`school-assets.service`) con arranque automático
- [x] Nginx en puerto 443 como proxy inverso
- [x] mDNS con Avahi — hostname `materiales` → `materiales.local`

**Entregable:** ✅ Se puede sacar y devolver material con el móvil en `https://materiales.local`

---

### Fase 2 — Panel de Administración ✅ *Completada*

**Objetivo:** gestionar todos los datos desde el portátil.

- [x] CRUD completo de usuarios
- [x] CRUD completo de categorías con árbol jerárquico
- [x] CRUD completo de material
- [x] Generación de QR individual (PNG) al crear material
- [x] Generación de PDF con lote de etiquetas (`GET /material/pdf-etiquetas`) — cuadrícula 3×N en A4
- [x] Listado de préstamos activos
- [x] Historial de movimientos con filtros (tipo, fecha_desde, fecha_hasta, usuario)
- [x] **Certificados mkcert** — CA local, sin advertencias en navegador, `rootCA.pem` descargable en `http://materiales.local/rootCA.pem`

**Entregable:** ✅ El administrador gestiona todo desde el panel web; etiquetas imprimibles en PDF

---

### Fase 3 — Pulido y Robustez *(en curso)*

**Objetivo:** el sistema es fiable y cómodo de usar en el día a día.

- [ ] Búsqueda de usuarios por nombre en el móvil
- [ ] Exportar historial a CSV desde el panel
- [ ] Alertas visuales para material prestado hace más de N días
- [ ] Tests automáticos de los endpoints críticos
- [ ] Script de backup automático de la base de datos
- [ ] README de uso completo

**Entregable:** sistema listo para producción.

---

### Fase 4 — Mejoras Opcionales *(backlog)*

- [ ] Foto del material (subida de imagen)
- [ ] PWA (Progressive Web App) para uso offline en el móvil
- [ ] Notificaciones de préstamos vencidos
- [ ] Estadísticas de uso por material y usuario
- [ ] Exportar informes a PDF
- [ ] Múltiples aulas / espacios

---

## 11. Instalación y Despliegue

### Requisitos Previos
- Ubuntu 22.04 LTS
- Python 3.10+
- Poetry (`curl -sSL https://install.python-poetry.org | python3 -`)
- Acceso a la red WiFi local

### Instalación desde cero

```bash
# 1. Certificado SSL con mkcert (sin advertencias en el navegador)
sudo bash scripts/setup_mkcert.sh

# 2. mDNS — materiales.local visible en la WiFi
sudo bash scripts/setup_avahi.sh

# 3. Nginx en puerto 443 → FastAPI en 8000
sudo bash scripts/setup_nginx.sh

# 4. Servicio systemd (arranca con el sistema)
sudo cp scripts/school-assets.service /etc/systemd/system/
sudo systemctl enable --now school-assets
```

### Acceso desde el Móvil

1. Conectar el móvil a la misma WiFi que el servidor
2. Instalar el root CA **una sola vez**: descargar `http://materiales.local/rootCA.pem`
   - **iOS**: Safari → descargar → Ajustes → Instalar perfil → Confianza de certificados
   - **Android**: usar Firefox; instalar CA en Ajustes del sistema
3. Abrir: `https://materiales.local`

### Variables de Entorno (`.env`)

```ini
DATABASE_URL=sqlite:///./data/assets.db
QR_BASE_URL=https://materiales.local
QR_IMAGES_DIR=./static/qr
```

---

## 12. Requisitos de Hardware

### Servidor (MiniPC o Portátil)

| Especificación | Mínimo | Recomendado |
|---|---|---|
| CPU | Cualquier dual-core moderno | — |
| RAM | 1 GB disponible | 2 GB |
| Almacenamiento | 10 GB libres | 20 GB (fotos futuras) |
| Sistema Operativo | Windows 10, Ubuntu 22.04, Raspberry Pi OS | Ubuntu 22.04 LTS |
| Red | WiFi o Ethernet | Ethernet para más estabilidad |

> ✅ Una **Raspberry Pi 4** (2 GB RAM) es completamente suficiente y muy económica.

### Teléfono Móvil (Escáner)

| Especificación | Requisito |
|---|---|
| Cámara trasera | Sí (autofocus recomendado) |
| Navegador | Chrome 88+, Safari 14+, Firefox 85+ |
| Conexión | WiFi (misma red que el servidor) |
| Sistema Operativo | Android 8+ o iOS 14+ |

### Impresora (Etiquetas QR)

| Tipo | Observaciones |
|---|---|
| Láser o inkjet estándar | Vale cualquiera, imprimir en papel y pegar |
| Impresora de etiquetas térmicas | Ideal (ej: Brother QL, DYMO) — imprime directamente en etiquetas adhesivas |

---

## 13. Seguridad y Backups

### Seguridad en Red Local

- El sistema **no está expuesto a internet**, solo a la red local del centro.
- Se usa **HTTPS con certificado mkcert** (CA local propia), que elimina las advertencias de seguridad del navegador una vez instalado el `rootCA.pem` en el dispositivo.
- El `rootCA.pem` se sirve en **HTTP** en `http://materiales.local/rootCA.pem` para facilitar su instalación (el resto del tráfico HTTP redirige a HTTPS).
- No hay sistema de login por defecto (entorno de confianza). Se puede añadir en Fase 4.

### Backup de la Base de Datos

La base de datos es un único fichero: `data/assets.db`. Para hacer backup basta con copiar ese fichero.

**Script de backup automático (cron):**
```bash
# Backup diario a las 22:00, guarda los últimos 30 días
0 22 * * * cp /home/usuario/school-assets/data/assets.db \
  /home/usuario/backups/assets_$(date +\%Y\%m\%d).db && \
  find /home/usuario/backups/ -name "assets_*.db" -mtime +30 -delete
```

**Backup manual rápido:**
```bash
cp data/assets.db backups/assets_manual_$(date +%Y%m%d_%H%M).db
```

---

## 14. Mejoras Futuras

| Mejora | Descripción | Prioridad |
|---|---|---|
| **Fotos de material** | Subir foto al crear/editar material, mostrar miniatura en inventario | Media |
| **PWA offline** | El móvil puede registrar movimientos sin conexión y sincronizar luego | Baja |
| **Alertas de préstamo vencido** | Avisar si un objeto lleva más de N días prestado | Media |
| **Login de usuarios** | Sistema de autenticación para que solo usuarios autorizados operen | Media |
| **Múltiples aulas** | Soporte para gestionar varias aulas o espacios independientes | Baja |
| **App móvil nativa** | App Android/iOS para mejor experiencia de escáner | Baja |
| **Estadísticas** | Dashboard con materiales más usados, usuarios más activos, etc. | Baja |
| **Exportar informes** | Generar informes PDF/Excel del inventario y movimientos | Media |
| **Escáner de barras** | Compatibilidad con lectores de código de barras USB (más rápidos) | Media |

---

## 15. Despliegue en Cloud (AWS)

### 15.1 ¿Cuándo tiene sentido el Cloud?

El despliegue local (MiniPC en el aula) es suficiente para un solo centro. Sin embargo, el cloud aporta valor en estos escenarios:

| Escenario | ¿Cloud recomendado? |
|---|---|
| Una sola aula, uso interno | ❌ Local es más simple y barato |
| Acceso desde casa / fuera del centro | ✅ Cloud elimina problemas de VPN/IP dinámica |
| Varios centros o aulas compartiendo datos | ✅ Base de datos centralizada en la nube |
| Sin nadie para mantener un servidor local | ✅ Cloud reduce mantenimiento |
| Presupuesto muy ajustado | ❌ Local es gratuito en infraestructura |

---

### 15.2 Arquitectura Cloud en AWS

#### Opción A — Mínima (1 sola instancia EC2)

La más sencilla y económica. Replica exactamente la arquitectura local pero en la nube.

```
Internet
    │
    ▼
┌─────────────────────────────────────┐
│  AWS                                │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  EC2 t4g.micro (ARM)        │    │
│  │  Ubuntu 24.04               │    │
│  │                             │    │
│  │  FastAPI + Uvicorn          │    │
│  │  SQLite (en disco EBS)      │    │
│  │  Nginx (proxy SSL)          │    │
│  └──────────────┬──────────────┘    │
│                 │                   │
│  ┌──────────────▼──────────────┐    │
│  │  EBS Volume (10 GB)         │    │
│  │  /data/assets.db            │    │
│  └─────────────────────────────┘    │
│                                     │
│  Route 53 (DNS) — opcional          │
│  ACM Certificate (SSL gratis)       │
└─────────────────────────────────────┘
         │
         ▼
  📱 Móvil  💻 Portátil  🏠 Casa
  (cualquier dispositivo con navegador)
```

#### Opción B — Escalable (EC2 + RDS)

Reemplaza SQLite por PostgreSQL gestionado (RDS). Apropiado si se gestionan varios centros o se prevé crecimiento.

```
Internet
    │
    ▼ (HTTPS)
┌───────────────────────────────────────────┐
│  AWS                                      │
│                                           │
│  Application Load Balancer (ALB)          │
│            │                              │
│            ▼                              │
│  ┌─────────────────────┐                  │
│  │  EC2 t4g.small      │                  │
│  │  FastAPI + Uvicorn  │                  │
│  └──────────┬──────────┘                  │
│             │                             │
│             ▼                             │
│  ┌─────────────────────┐                  │
│  │  RDS PostgreSQL      │                  │
│  │  db.t4g.micro        │                  │
│  └─────────────────────┘                  │
│                                           │
│  S3 (imágenes QR y PDFs generados)        │
│  ACM Certificate (SSL gratuito)           │
└───────────────────────────────────────────┘
```

---

### 15.3 Cambios en el Stack para Cloud

| Componente | Local | Cloud (Opción A) | Cloud (Opción B) |
|---|---|---|---|
| Base de datos | SQLite | SQLite en EBS | PostgreSQL (RDS) |
| SSL | Certificado autofirmado | ACM (Let's Encrypt vía Nginx) | ACM + ALB |
| Almacenamiento ficheros QR | Disco local | EBS | S3 |
| Backups | Script cron manual | AWS Backup / snapshot EBS | RDS automated backups |
| DNS | IP local fija | Route 53 o dominio propio | Route 53 |

Para la **Opción A**, el código prácticamente no cambia: solo se añade Nginx como proxy inverso delante de FastAPI para gestionar el certificado SSL de Let's Encrypt.

Para la **Opción B**, se cambia la `DATABASE_URL` en `.env` de SQLite a PostgreSQL y se añade `psycopg2` a las dependencias. SQLAlchemy abstrae el resto.

---

### 15.4 Estimación de Costes AWS

> Los precios corresponden a la región **eu-west-1 (Irlanda)**, que es la más cercana a España. Precios aproximados a marzo 2026.

#### Opción A — Mínima (EC2 t4g.micro + EBS)

| Servicio | Especificación | Coste/mes |
|---|---|---|
| EC2 t4g.micro | 2 vCPU ARM, 1 GB RAM | **~8,40 €** |
| EBS gp3 | 10 GB almacenamiento | **~0,90 €** |
| Transferencia de datos | < 1 GB/mes (uso interno) | **~0,00 €** |
| Route 53 | 1 zona DNS (opcional) | **~0,50 €** |
| **Total Opción A** | | **~9,80 € / mes** |

> 💡 **Con Reserved Instance (1 año):** el EC2 t4g.micro baja a ~5,50 €/mes → **total ~7 €/mes**

#### Opción B — Escalable (EC2 + RDS)

| Servicio | Especificación | Coste/mes |
|---|---|---|
| EC2 t4g.small | 2 vCPU ARM, 2 GB RAM | **~16,80 €** |
| RDS PostgreSQL db.t4g.micro | 2 vCPU, 1 GB RAM, 20 GB storage | **~18,50 €** |
| S3 Standard | 5 GB (imágenes QR) | **~0,12 €** |
| ALB | Application Load Balancer | **~18,00 €** |
| Route 53 | 1 zona DNS | **~0,50 €** |
| **Total Opción B** | | **~53,90 € / mes** |

> 💡 **Sin ALB** (usando Nginx en el EC2 directamente): baja a **~36 €/mes**

#### Opción Serverless (AWS Lambda + DynamoDB) — No recomendada

| Servicio | Coste/mes estimado |
|---|---|
| Lambda (requests de la API) | < 1 € (uso bajo) |
| DynamoDB | ~5 € |
| API Gateway | ~3 € |
| **Total** | **~9 €/mes** |

> ⚠️ **Por qué no se recomienda:** requiere reescribir completamente el backend (FastAPI no encaja bien en Lambda sin adaptadores), DynamoDB implica rediseñar el modelo de datos, y la complejidad operativa no compensa el ahorro para este volumen de uso.

#### Comparativa de Opciones

```
                    Coste/mes    Complejidad    Escalabilidad
                    ─────────    ───────────    ─────────────
Local (MiniPC)       0 € *          Baja            Ninguna
AWS Opción A        ~10 €           Baja            Media
AWS Opción B        ~54 €           Media           Alta
AWS Serverless       ~9 €           Alta            Alta

* Sin contar el coste del hardware (~150-300 € amortizado)
```

#### Coste Anual Estimado

| Opción | Coste anual | Notas |
|---|---|---|
| Local | ~0 € / año | Hardware ~200 € inversión inicial |
| AWS Opción A | ~118 € / año | Con Reserved Instance ~84 €/año |
| AWS Opción B | ~647 € / año | Con Reserved Instances ~450 €/año |

---

### 15.5 Despliegue Paso a Paso en AWS (Opción A)

```bash
# 1. Lanzar instancia EC2
#    - AMI: Ubuntu 24.04 LTS ARM64
#    - Tipo: t4g.micro
#    - Almacenamiento: 10 GB gp3
#    - Security Group: puertos 22 (SSH), 80 (HTTP), 443 (HTTPS)

# 2. Conectar por SSH
ssh -i mi-clave.pem ubuntu@<IP_PUBLICA>

# 3. Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3.11 python3-pip nginx certbot python3-certbot-nginx

# 4. Clonar proyecto y configurar entorno
git clone <repositorio> /opt/school-assets
cd /opt/school-assets
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configurar servicio systemd (igual que despliegue local)
sudo cp deploy/school-assets.service /etc/systemd/system/
sudo systemctl enable school-assets
sudo systemctl start school-assets

# 6. Configurar Nginx como proxy inverso
sudo cp deploy/nginx.conf /etc/nginx/sites-available/school-assets
sudo ln -s /etc/nginx/sites-available/school-assets /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Obtener certificado SSL gratuito con Let's Encrypt
sudo certbot --nginx -d mi-dominio.com

# 8. El certificado se renueva automáticamente cada 90 días
```

**Fichero `deploy/nginx.conf`:**
```nginx
server {
    server_name mi-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSL gestionado por certbot automáticamente
}
```

---

### 15.6 Backups en AWS

#### Opción A (SQLite en EBS)
```bash
# Snapshot diario del volumen EBS (via AWS CLI o consola)
# O backup del fichero a S3:
aws s3 cp /opt/school-assets/data/assets.db \
  s3://mi-bucket-backups/assets_$(date +%Y%m%d).db

# Añadir al cron:
0 22 * * * aws s3 cp /opt/school-assets/data/assets.db s3://mi-bucket-backups/assets_$(date +\%Y\%m\%d).db
```
Coste de S3 para backups (30 ficheros × ~1 MB): **< 0,01 €/mes** — prácticamente gratis.

#### Opción B (RDS PostgreSQL)
RDS ofrece backups automáticos diarios con retención configurable (hasta 35 días) incluidos en el precio. No requiere configuración adicional.

---

### 15.7 Seguridad Adicional en Cloud

A diferencia del despliegue local, en cloud el sistema es accesible desde internet, por lo que se deben tomar precauciones adicionales:

| Medida | Descripción | Coste |
|---|---|---|
| **HTTPS obligatorio** | Nginx redirige HTTP → HTTPS automáticamente | Gratis (Let's Encrypt) |
| **Sistema de login** | Añadir autenticación básica (usuario/contraseña) a la app | Desarrollo |
| **Security Group restrictivo** | Solo puertos 80 y 443 abiertos; SSH solo desde IP del administrador | Gratis |
| **AWS WAF** (opcional) | Firewall de aplicación web contra ataques | ~6 €/mes |
| **Actualizaciones automáticas** | `unattended-upgrades` en Ubuntu para parches de seguridad | Gratis |
| **Fail2ban** | Bloquea IPs con intentos de acceso repetidos | Gratis |

> ⚠️ **Importante:** en cloud es **imprescindible** añadir al menos un sistema de login básico a la aplicación antes de desplegarla, ya que cualquier persona con la URL podría registrar movimientos.

---

### 15.8 Recomendación Final: Local vs Cloud

```
┌──────────────────────────────────────────────────────────────┐
│  ¿Una sola aula, acceso solo desde el centro?                │
│                         │                                    │
│                    SÍ ──┤──► LOCAL (MiniPC/Raspberry Pi)     │
│                         │    Coste: ~0 €/mes                 │
│                         │    Simple, rápido, sin internet    │
│                    NO   │                                    │
│                         ▼                                    │
│  ¿Necesitas acceso desde fuera o varios centros?             │
│                         │                                    │
│              ACCESO ────┤──► AWS Opción A (~10 €/mes)        │
│              REMOTO     │    EC2 + SQLite + Nginx + SSL      │
│                         │                                    │
│           MÚLTIPLES ────┘──► AWS Opción B (~54 €/mes)        │
│            CENTROS           EC2 + RDS PostgreSQL            │
└──────────────────────────────────────────────────────────────┘
```

Para la mayoría de los colegios con una sola aula, **la opción local sigue siendo la más recomendada**: cero coste mensual, sin dependencia de internet, y toda la complejidad operativa se elimina. Si en el futuro surge la necesidad de acceso remoto, migrar de local a AWS Opción A es sencillo porque la arquitectura y el código son prácticamente idénticos.

---

## Apéndice A — Dependencias Python (`requirements.txt`)

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.29
alembic==1.13.1
pydantic==2.7.0
qrcode[pil]==7.4.2
Pillow==10.3.0
python-dotenv==1.0.1
reportlab==4.1.0       # Generación de PDF de etiquetas
pytest==8.1.1
httpx==0.27.0          # Cliente HTTP para tests
```

---

## Apéndice B — Variables de Entorno (`.env.example`)

```env
# Puerto del servidor
PORT=8000

# Ruta al fichero de base de datos SQLite
DATABASE_URL=sqlite:///./data/assets.db

# Prefijo para los códigos QR (ej: MAT → MAT-00001)
QR_PREFIX=MAT

# Días sin devolver antes de mostrar alerta
ALERTA_DIAS_PRESTAMO=7

# Ruta a los certificados SSL (autofirmados)
SSL_KEYFILE=./certs/cert.key
SSL_CERTFILE=./certs/cert.crt
```

---

*Documento generado: Marzo 2026 — v1.1*
