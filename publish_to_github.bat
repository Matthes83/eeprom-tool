@echo off
REM ===================================================================
REM  Veroeffentlicht dieses Verzeichnis als GitHub-Repository (Windows).
REM  Nutzt die GitHub CLI (gh). Doppelklick genuegt.
REM
REM  Voraussetzung: GitHub CLI installiert (https://cli.github.com)
REM  Standard: Repo-Name "eeprom-tool", oeffentlich.
REM ===================================================================
setlocal

set REPO_NAME=eeprom-tool
set VISIBILITY=public

echo.
echo === Veroeffentlichung auf GitHub ===
echo Repository: %REPO_NAME%  (%VISIBILITY%)
echo.

where gh >nul 2>&1
if errorlevel 1 (
    echo FEHLER: GitHub CLI ^(gh^) ist nicht installiert.
    echo Installieren: https://cli.github.com
    pause
    exit /b 1
)

gh auth status >nul 2>&1
if errorlevel 1 (
    echo Noch nicht angemeldet. Starte Login ...
    gh auth login
)

if not exist .git (
    git init
    git branch -M main
)

git add .
git commit -m "24C EEPROM Tool - erste Veroeffentlichung"

gh repo create %REPO_NAME% --%VISIBILITY% --source=. --remote=origin --push

echo.
echo === FERTIG ===
echo Repository online. Oeffnen mit:  gh repo view --web
echo.
echo Tipp: Release mit fertiger .exe/.app:
echo   git tag v1.0.0  ^&^&  git push origin v1.0.0
echo.
pause
