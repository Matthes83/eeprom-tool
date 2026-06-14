# Anleitung: Auf GitHub veröffentlichen

Dieses Verzeichnis ist ein fertiges Repository. Du musst es nur noch zu deinem
GitHub-Konto hochladen. Es gibt zwei Wege – wähle einen.

---

## Voraussetzungen (einmalig)

1. **Git** installiert – Test im Terminal: `git --version`
   Falls nicht: https://git-scm.com/downloads
2. **GitHub CLI** installiert – Test: `gh --version`
   Falls nicht: https://cli.github.com
3. Ein **GitHub-Konto**.

---

## Weg 1 – Automatisch per Skript (empfohlen)

Im Terminal in **dieses Verzeichnis** wechseln, dann:

**macOS / Linux:**
```bash
chmod +x publish_to_github.sh
./publish_to_github.sh eeprom-tool public
```

**Windows:**
Doppelklick auf `publish_to_github.bat`
(oder im Terminal `publish_to_github.bat`).

Das Skript meldet dich bei GitHub an (falls noch nicht geschehen), legt das
Repository an und lädt alles hoch. Beim ersten Mal öffnet sich für den Login
ein Browserfenster – dort bestätigen, fertig.

Den Repo-Namen oder die Sichtbarkeit kannst du anpassen:
```bash
./publish_to_github.sh mein-eeprom-tool private
```

---

## Weg 2 – Manuell, Schritt für Schritt

Falls du lieber jeden Schritt selbst machst:

```bash
# 1. Bei GitHub anmelden (einmalig, öffnet den Browser)
gh auth login

# 2. In dieses Verzeichnis wechseln
cd pfad/zu/diesem/ordner

# 3. Git-Repository initialisieren
git init
git branch -M main
git add .
git commit -m "24C EEPROM Tool - erste Veröffentlichung"

# 4. Repository auf GitHub anlegen und hochladen
gh repo create eeprom-tool --public --source=. --remote=origin --push
```

Danach ist das Projekt online. Mit `gh repo view --web` öffnest du es im
Browser.

---

## Nach dem Hochladen: Fertige Programme bauen lassen

Sobald das Repo online ist, baut GitHub auf Wunsch automatisch die fertige
`.exe` und `.app` – ganz ohne eigenen Build auf deinem Rechner.

**Automatischer Build bei jeder Änderung:**
Läuft von selbst bei jedem Push auf `main`. Ergebnisse findest du auf der
GitHub-Seite unter dem Reiter **Actions** → neuester Lauf → **Artifacts**.

**Veröffentlichtes Release mit Download-Dateien:**
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub baut dann beide Programme und legt sie unter **Releases** zum Download
ab. Genau dorthin verweist auch der Download-Link in der README.

---

## Später Änderungen hochladen

```bash
git add .
git commit -m "Beschreibung der Änderung"
git push
```

---

## Häufige Stolpersteine

- **`gh: command not found`** – GitHub CLI ist nicht installiert oder nicht im
  PATH. Terminal nach der Installation neu öffnen.
- **Login klappt nicht** – `gh auth login` erneut ausführen und „GitHub.com“ →
  „HTTPS“ → „Browser“ wählen.
- **`repository already exists`** – ein Repo mit dem Namen existiert schon.
  Anderen Namen wählen oder das alte auf GitHub löschen.
- **Actions-Build schlägt fehl** – prüfen, ob alle Dateien (besonders
  `requirements.txt` und `eeprom.spec`) im Repo liegen. Der Reiter **Actions**
  zeigt das genaue Fehlerprotokoll.
