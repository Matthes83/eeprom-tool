#!/bin/bash
# ===================================================================
#  Build-Skript fuer macOS  -  erzeugt dist/EEPROM-Tool.app
#  Aufruf:  ./build_mac.sh   (ggf. vorher: chmod +x build_mac.sh)
#  Python 3.9+ muss installiert sein (z.B. via python.org oder brew).
# ===================================================================
set -e

echo ""
echo "=== 24C EEPROM Tool - macOS Build ==="
echo ""

# Python finden
if ! command -v python3 >/dev/null 2>&1; then
    echo "FEHLER: python3 nicht gefunden. Bitte von python.org installieren."
    exit 1
fi

# Virtuelle Umgebung
if [ ! -d ".venv" ]; then
    echo "Erstelle virtuelle Umgebung ..."
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "Installiere Abhaengigkeiten ..."
python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install -r requirements.txt

echo ""
echo "Baue .app ..."
pyinstaller --clean --noconfirm eeprom.spec

echo ""
echo "=== FERTIG ==="
echo "Die Anwendung liegt unter:  dist/EEPROM-Tool.app"
echo ""
echo "Hinweis: Beim ersten Start meldet macOS evtl. 'nicht verifizierter"
echo "Entwickler'. Dann Rechtsklick auf die App -> Oeffnen -> Oeffnen,"
echo "oder in den Systemeinstellungen unter Datenschutz/Sicherheit freigeben."
echo ""
echo "Fuer den seriellen Zugriff sind keine Extra-Rechte noetig; die"
echo "Ports erscheinen als /dev/cu.usbserial-* bzw. /dev/cu.usbmodem-*."
