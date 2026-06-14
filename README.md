# 24C EEPROM Tool

Ein Werkzeug zum Auslesen und Beschreiben von I²C-EEPROMs der **24er-Serie**
(24C01 bis 24C512) über einen Arduino. Mit grafischer Oberfläche,
automatischer Chip-Erkennung, Hex-Vorschau und bin-Dump Import/Export.

![Plattform](https://img.shields.io/badge/Plattform-Windows%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-green)
![Lizenz](https://img.shields.io/badge/Lizenz-MIT-lightgrey)

---

## Funktionen

- Auslesen eines kompletten EEPROM-Inhalts als `.bin`-Datei
- Zurückschreiben einer `.bin`-Datei auf den Chip
- Automatische Chip-Erkennung per Adress-Wrap-Around-Test
- Manuelle Chip-Auswahl (24C01 … 24C512) als Fallback
- Hex-Vorschau des gelesenen oder geladenen Inhalts
- Eigenständige Anwendung für Windows (`.exe`) und macOS (`.app`),
  kein Python auf dem Zielrechner nötig

---

## Inhalt des Repos

| Datei                          | Zweck                                        |
|--------------------------------|----------------------------------------------|
| `eeprom_firmware.ino`          | Arduino-Firmware                             |
| `eeprom_gui.py`                | Hauptprogramm (GUI)                          |
| `eeprom.spec`                  | PyInstaller-Konfiguration                    |
| `requirements.txt`             | Python-Abhängigkeiten                        |
| `build_windows.bat`            | One-Klick-Build → `.exe`                     |
| `build_mac.sh`                 | One-Klick-Build → `.app`                     |
| `.github/workflows/build.yml`  | Automatischer Build für Windows + macOS      |

---

## Schnellstart

### 1. Hardware verdrahten

DIP-8 EEPROM an einen Arduino UNO:

```
EEPROM            Arduino UNO
 A0, A1, A2  ───  GND
 GND (4)     ───  GND
 SDA (5)     ───  A4   (+ 4,7 kΩ Pull-up nach 5V)
 SCL (6)     ───  A5   (+ 4,7 kΩ Pull-up nach 5V)
 WP  (7)     ───  GND
 VCC (8)     ───  5V
```

> Die beiden 4,7-kΩ-Pull-up-Widerstände an SDA und SCL sind zwingend
> erforderlich – ohne sie funktioniert der I²C-Bus nicht zuverlässig.

### 2. Firmware aufspielen

`eeprom_firmware.ino` in der Arduino IDE öffnen und auf den Arduino UNO
hochladen.

### 3. Anwendung beziehen

**Variante A – fertige Datei herunterladen** (empfohlen):
Unter [Releases](../../releases) die passende Datei für dein System laden.
Falls noch kein Release existiert, siehe Variante B.

**Variante B – selbst bauen:**

- **Windows:** Doppelklick auf `build_windows.bat` → erzeugt `dist\EEPROM-Tool.exe`
- **macOS:** im Terminal:
  ```bash
  chmod +x build_mac.sh
  ./build_mac.sh
  ```
  → erzeugt `dist/EEPROM-Tool.app`

> Eine `.exe` lässt sich nur unter Windows bauen, eine `.app` nur unter macOS.
> PyInstaller erzeugt keine plattformübergreifenden Binärdateien. Wer beide
> braucht, nutzt den GitHub-Actions-Workflow (siehe unten), der beide parallel
> baut.

### 4. Bedienung

1. Arduino anstecken, Anwendung starten.
2. **Port** auswählen (Windows: `COMx`, macOS: `/dev/cu.usbmodem…`) und
   **Verbinden** drücken.
3. **Auto-Erkennen** klicken oder den **Chip** manuell aus der Liste wählen.
4. **Auslesen → Datei** speichert den Dump als `.bin`.
   **bin laden** + **Datei → Schreiben** schreibt eine Datei zurück.

---

## Automatischer Build über GitHub Actions

Der mitgelieferte Workflow `.github/workflows/build.yml` baut bei jedem Push
auf `main` automatisch beide Varianten. Die Ergebnisse erscheinen unter dem
Reiter **Actions** als herunterladbare Artefakte.

Für ein **veröffentlichtes Release** mit angehängten Dateien genügt ein Tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Der Workflow baut dann `.exe` und `.app`, erstellt ein GitHub-Release und
hängt beide Dateien an.

---

## Unterstützte Chips

| Typ     | Größe   | Adressbytes |
|---------|---------|-------------|
| 24C01   | 128 B   | 1           |
| 24C02   | 256 B   | 1           |
| 24C04   | 512 B   | 1           |
| 24C08   | 1 KB    | 1           |
| 24C16   | 2 KB    | 1           |
| 24C32   | 4 KB    | 2           |
| 24C64   | 8 KB    | 2           |
| 24C128  | 16 KB   | 2           |
| 24C256  | 32 KB   | 2           |
| 24C512  | 64 KB   | 2           |

### Hinweis zur automatischen Erkennung

Die Erkennung beruht auf einem Spiegelungs-Test: Bei kleineren Chips wiederholt
sich der Inhalt, wenn man über das Adressende hinaus liest. Bei einem
**beschriebenen** Chip ist das treffsicher. Ein **leerer** Chip ist überall
`0xFF` und sieht damit aus wie der kleinste Typ – in dem Fall den Typ manuell
wählen.

---

## Voraussetzungen für den Build

Python 3.9 oder neuer auf dem Build-Rechner. Die Build-Skripte legen
automatisch eine virtuelle Umgebung an und installieren `pyserial` und
`pyinstaller` selbst. Auf dem **Zielrechner** ist nichts weiter nötig.

---

## Lizenz

MIT – siehe [LICENSE](LICENSE).
