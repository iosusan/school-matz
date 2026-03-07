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

Para ejecutarlo manualmente sobre todos los ficheros:

```bash
pre-commit run --all-files
```

---

## Conventional Commits

El hook `commit-msg` rechaza mensajes que no sigan el formato:

```
<tipo>(<scope>): <descripción>
```

**Tipos permitidos:** `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore` · `ci` · `perf` · `build`

Ejemplos válidos:

```
feat(usuarios): añade filtro por curso
fix(api): corrige paginación en listado de materiales
chore(deps): actualiza ruff a 0.16
docs: actualiza README_DEV
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
