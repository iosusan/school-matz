# Guía de desarrollo

## Configuración del entorno

```bash
poetry install --with dev
poetry shell
pre-commit install
pre-commit install --hook-type commit-msg
```

---

## pre-commit

Se ejecuta automáticamente en cada `git commit`. Incluye:

| Hook | Acción |
|---|---|
| `ruff` | Linter — corrige errores automáticamente |
| `ruff-format` | Formatter |
| `gitlint` | Valida el mensaje de commit (conventional commits) |
| `trailing-whitespace` | Elimina espacios al final de línea |
| `end-of-file-fixer` | Asegura salto de línea final |
| `check-toml` / `check-yaml` | Valida sintaxis de ficheros de configuración |
| `debug-statements` | Detecta `breakpoint()` / `pdb` olvidados |
| `pip-audit` *(pre-push)* | Audita dependencias contra CVEs conocidos (OSV) |

Para ejecutarlo manualmente sobre todos los ficheros:

```bash
pre-commit run --all-files                          # hooks de pre-commit
pre-commit run pip-audit --hook-stage pre-push      # auditoría de dependencias
```

---

## Conventional Commits

El hook `gitlint` valida cada mensaje de commit contra esta regex (definida en `.gitlint`):

```
^(feat|fix|docs|style|refactor|test|chore|ci|perf|build)(\([a-z0-9/_-]+\))?!?: .+
```

### Formato

```
<tipo>(<scope>): <descripción>
  │       │           └─ texto libre, minúsculas o mayúsculas, sin punto final obligatorio
  │       └─ opcional — módulo o área afectada, en minúsculas (letras, números, / _ -)
  └─ obligatorio — uno de los tipos de la tabla de abajo
```

Para indicar un **breaking change** se añade `!` antes de los dos puntos:

```
feat(api)!: cambia estructura de respuesta de /usuarios
```

### Tipos permitidos

| Tipo | Cuándo usarlo | Aparece en CHANGELOG |
|---|---|---|
| `feat` | Nueva funcionalidad | ✅ **Features** |
| `fix` | Corrección de bug | ✅ **Bug Fixes** |
| `perf` | Mejora de rendimiento | ✅ **Performance** |
| `refactor` | Refactoring sin cambio de comportamiento | ✅ **Refactoring** |
| `docs` | Cambios en documentación | ✅ **Documentation** |
| `test` | Añadir o corregir tests | ✅ **Tests** |
| `ci` | Cambios en pipelines CI/CD | ✅ **CI/CD** |
| `build` | Sistema de build, dependencias | ✅ **Build** |
| `chore` | Tareas de mantenimiento | ✅ **Miscellaneous** |
| `style` | Formato, espacios, punto y coma | ❌ omitido |

### Ejemplos válidos

```
feat(usuarios): añade filtro por curso
fix(api): corrige paginación en listado de materiales
refactor(pdf): extrae lógica de color a función auxiliar
docs: actualiza README_DEV con sección de commits
test(modelos): añade tests de validación de Usuario
chore(deps): actualiza ruff a 0.16
ci: añade workflow de build Docker en GitHub Actions
feat(auth)!: requiere token en todas las rutas de la API
```

### Ejemplos inválidos (el hook rechazará el commit)

```
# ❌ tipo no reconocido
update: mejoras varias

# ❌ falta la descripción
feat(api):

# ❌ scope con mayúsculas
fix(Auth): corrige login

# ❌ sin tipo
corrige bug en el listado
```

---

## Releases — `release.sh`

### Uso

```bash
./release.sh <major|minor|patch>
```

### Qué hace el script

1. Lee la versión actual de `pyproject.toml`
2. Calcula la nueva versión según el tipo de bump
3. Actualiza `version = "..."` en `pyproject.toml`
4. Genera `CHANGELOG.md` con `git-cliff` (agrupa commits por tipo)
5. Hace `git commit` con el mensaje `chore(release): vX.Y.Z`
6. Crea el tag `vX.Y.Z`
7. Ejecuta `git push && git push --tags`

### Ejemplos

```bash
./release.sh patch   # 0.1.0 → 0.1.1  (bug fixes)
./release.sh minor   # 0.1.0 → 0.2.0  (nuevas funcionalidades)
./release.sh major   # 0.1.0 → 1.0.0  (cambios incompatibles)
```

### Notas

- El commit de release **bypasea** el hook `commit-msg` (es generado por el script).
- El `CHANGELOG.md` se genera automáticamente a partir de los commits desde el tag anterior.
- Los commits de tipo `style` y `chore(release)` se omiten del changelog.
- Para ver una preview del changelog sin hacer release: `git-cliff --unreleased`


### mirror dockerhub
Por si hay futbol...

dockerhub.timeweb.cloud

https://gist.github.com/b4tman/2424015efb60eb2bd3b9c60f53de6ffe
