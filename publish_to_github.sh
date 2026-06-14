#!/bin/bash
# ===================================================================
#  Veroeffentlicht dieses Verzeichnis als GitHub-Repository.
#  Nutzt die GitHub CLI (gh). Einmal ausfuehren - fertig.
#
#  Voraussetzung: GitHub CLI installiert (https://cli.github.com)
#  Aufruf:  ./publish_to_github.sh [repo-name] [public|private]
#  Beispiel: ./publish_to_github.sh eeprom-tool public
# ===================================================================
set -e

REPO_NAME="${1:-eeprom-tool}"
VISIBILITY="${2:-public}"

echo ""
echo "=== Veroeffentlichung auf GitHub ==="
echo "Repository: $REPO_NAME  ($VISIBILITY)"
echo ""

# 1) gh vorhanden?
if ! command -v gh >/dev/null 2>&1; then
    echo "FEHLER: GitHub CLI (gh) ist nicht installiert."
    echo "Installieren: https://cli.github.com"
    exit 1
fi

# 2) Eingeloggt?
if ! gh auth status >/dev/null 2>&1; then
    echo "Noch nicht bei GitHub angemeldet. Starte Login ..."
    gh auth login
fi

# 3) git-Repo initialisieren, falls noetig
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

git add .
git commit -m "24C EEPROM Tool - erste Veroeffentlichung" || \
    echo "(nichts zu committen)"

# 4) Repo erstellen und pushen
gh repo create "$REPO_NAME" \
    --"$VISIBILITY" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "=== FERTIG ==="
echo "Dein Repository ist online. Oeffnen mit:  gh repo view --web"
echo ""
echo "Tipp: Fuer ein Release mit fertiger .exe/.app:"
echo "  git tag v1.0.0 && git push origin v1.0.0"
