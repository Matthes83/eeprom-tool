@echo off
REM ===================================================================
REM  Build-Skript fuer Windows  -  erzeugt dist\EEPROM-Tool.exe
REM  Doppelklick genuegt. Python 3.9+ muss installiert sein.
REM ===================================================================
setlocal

echo.
echo === 24C EEPROM Tool - Windows Build ===
echo.

REM Python finden
where python >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden. Bitte von python.org installieren
    echo und beim Setup "Add Python to PATH" anhaken.
    pause
    exit /b 1
)

REM Virtuelle Umgebung anlegen (isoliert die Build-Pakete)
if not exist .venv (
    echo Erstelle virtuelle Umgebung ...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo Installiere Abhaengigkeiten ...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER bei der Installation.
    pause
    exit /b 1
)

echo.
echo Baue EXE ...
pyinstaller --clean --noconfirm eeprom.spec
if errorlevel 1 (
    echo FEHLER beim Build.
    pause
    exit /b 1
)

echo.
echo === FERTIG ===
echo Die Anwendung liegt unter:  dist\EEPROM-Tool.exe
echo.
pause
