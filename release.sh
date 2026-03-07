#!/usr/bin/env bash
# release.sh — bumps version, generates changelog, commits, tags and pushes
# Usage: ./release.sh <major|minor|patch>

set -euo pipefail

BUMP="${1:-}"
if [[ "$BUMP" != "major" && "$BUMP" != "minor" && "$BUMP" != "patch" ]]; then
    echo "Usage: $0 <major|minor|patch>"
    exit 1
fi

PYPROJECT="pyproject.toml"

# ── 1. Read current version ───────────────────────────────────────────────────
CURRENT=$(grep -Po '(?<=^version = ")[^"]+' "$PYPROJECT")
if [[ -z "$CURRENT" ]]; then
    echo "Error: version not found in $PYPROJECT"
    exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# ── 2. Calculate new version ──────────────────────────────────────────────────
case "$BUMP" in
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    patch) PATCH=$((PATCH + 1)) ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
NEW_TAG="v${NEW_VERSION}"

echo "Bumping: ${CURRENT} → ${NEW_VERSION}"

# ── 3. Update version in pyproject.toml ──────────────────────────────────────
sed -i "s/^version = \"${CURRENT}\"/version = \"${NEW_VERSION}\"/" "$PYPROJECT"

# ── 4. Generate CHANGELOG.md ─────────────────────────────────────────────────
.venv/bin/git-cliff --tag "$NEW_TAG" -o CHANGELOG.md
# Asegurar exactamente un \n al final (end-of-file-fixer)
sed -i -e '$a\' CHANGELOG.md && sed -i -e '/^$/{ N; /^\n$/d }' /dev/null || true
printf '%s' "$(cat CHANGELOG.md | sed 's/[[:space:]]*$//' | sed -e :a -e '/^\n*$/{$d;N;ba}')" > CHANGELOG.md && echo >> CHANGELOG.md

# ── 5. Commit and tag ─────────────────────────────────────────────────────────
git add "$PYPROJECT" CHANGELOG.md
# GITLINT_SKIP=1 bypasses the commit-msg hook for this automated release commit
GITLINT_SKIP=1 git commit --no-verify -m "chore(release): ${NEW_TAG}"
git tag "$NEW_TAG"

# ── 6. Push ───────────────────────────────────────────────────────────────────
git push
git push --tags

echo "Released ${NEW_TAG}"
