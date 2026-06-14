#!/usr/bin/env python3
"""
24C-EEPROM Tool mit GUI und Auto-Erkennung.
Benoetigt: pip install pyserial
Firmware: eeprom_firmware.ino (mit 'S'-Set-Befehl)
"""
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import serial
import serial.tools.list_ports

# Bekannte 24C-Typen: Name -> (Groesse Bytes, Pagesize, Adressbytes)
CHIPS = {
    "24C01":  (128,    8, 1),
    "24C02":  (256,    8, 1),
    "24C04":  (512,   16, 1),
    "24C08":  (1024,  16, 1),
    "24C16":  (2048,  16, 1),
    "24C32":  (4096,  32, 2),
    "24C64":  (8192,  32, 2),
    "24C128": (16384, 64, 2),
    "24C256": (32768, 64, 2),
    "24C512": (65536, 128, 2),
}


class EEPROM:
    """Serielle Kommunikation mit der Arduino-Firmware."""

    def __init__(self, port, baud=115200, log=print):
        self.log = log
        self.s = serial.Serial(port, baud, timeout=5)
        time.sleep(2)               # Reset abwarten
        self.s.reset_input_buffer()

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

    def set_chip(self, size, page, addrbytes):
        self.s.reset_input_buffer()
        self.s.write(f"S {size} {page} {addrbytes}\n".encode())
        return self.s.readline().decode(errors="replace").strip()

    def autodetect(self):
        """
        Auto-Erkennung ueber den firmwareseitigen 'D'-Befehl.

        Die Firmware ermittelt hardwarenah:
          1. Adressbreite (1 vs 2 Byte) durch Vergleich von Byte 0 in
             beiden Modi - ein kleiner Chip liefert im 2-Byte-Modus Murks.
          2. Groesse durch zerstoerungsfreien Wrap-Around-Test (Marker
             schreiben, auf Adresse 0 pruefen, Original zuruecksichern).

        Das ist zuverlaessiger als eine reine Spiegelungs-Heuristik und
        funktioniert auch bei leeren Chips.

        Liefert (name, size, page, addrbytes) oder None.
        """
        self.log("Auto-Erkennung laeuft (Firmware-Detect) ...")
        self.s.reset_input_buffer()
        self.s.write(b"D")
        # Detect kann durch die Schreibzyklen einen Moment dauern
        line = self.s.readline().decode(errors="replace").strip()
        if not line.startswith("DETECT"):
            self.log(f"Unerwartete Antwort: {line!r}")
            return None

        # Format: "DETECT size=256 addrbytes=1 page=8"
        size = addrbytes = page = None
        for tok in line.split():
            if tok.startswith("size="):
                size = int(tok[5:])
            elif tok.startswith("addrbytes="):
                addrbytes = int(tok[10:])
            elif tok.startswith("page="):
                page = int(tok[5:])

        if size is None or addrbytes is None:
            self.log(f"Konnte Antwort nicht parsen: {line!r}")
            return None

        # passenden bekannten Chip-Namen suchen
        name = next((n for n, (sz, pg, ab) in CHIPS.items()
                     if sz == size and ab == addrbytes), None)
        if name is None:
            self.log(f"Erkannt: {size} Bytes, {addrbytes} Adressbyte(s) "
                     f"- kein Standardtyp, bitte pruefen.")
            return None

        self.log(f"Erkannt: {name} ({size} Bytes, "
                 f"{addrbytes} Adressbyte(s))")
        return (name, size, page or CHIPS[name][1], addrbytes)

    def read_dump(self, size, page, addrbytes):
        self.set_chip(size, page, addrbytes)
        self.s.reset_input_buffer()
        self.s.write(b"R")
        data = self.s.read(size)
        if len(data) != size:
            raise IOError(f"Nur {len(data)}/{size} Bytes gelesen")
        return data

    def write_dump(self, data, size, page, addrbytes):
        if len(data) != size:
            raise ValueError(f"Datei {len(data)} Bytes, Chip {size} Bytes")
        self.set_chip(size, page, addrbytes)
        self.s.reset_input_buffer()
        # Handshake: W senden, auf READY der Firmware warten, DANN Daten.
        # Das verhindert, dass alte Kommando-Bytes in die Daten geraten.
        self.s.write(b"W")
        self.s.flush()
        ready = self.s.readline().decode(errors="replace").strip()
        if ready != "READY":
            raise IOError(f"Kein READY von der Firmware (bekam: {ready!r})")
        # Jetzt die Datenbytes senden - flussgesteuert in 32-Byte-Bloecken.
        # Nach jedem Block wartet die GUI auf '.' der Firmware, bevor sie
        # weiterschickt. Verhindert Ueberlauf des 64-Byte-Arduino-Puffers.
        BLOCK = 32
        old_to = self.s.timeout
        self.s.timeout = max(old_to or 5, 15)
        try:
            sent = 0
            while sent < size:
                chunk = data[sent:sent + BLOCK]
                self.s.write(chunk)
                self.s.flush()
                ack = self.s.read(1)   # auf '.' warten
                if ack != b".":
                    # koennte schon die Schlussmeldung sein
                    rest = self.s.readline().decode(errors="replace")
                    full = (ack.decode(errors="replace") + rest).strip()
                    if full.startswith("TIMEOUT"):
                        raise IOError(
                            f"Firmware bekam nicht alle Bytes: {full}. "
                            f"Pruefe uC-Reset und WP-Pin.")
                    raise IOError(f"Block-Quittung fehlt (bekam: {full!r})")
                sent += len(chunk)
            # alle Bloecke bestaetigt -> Schlussmeldung lesen
            resp = self.s.readline().decode(errors="replace").strip()
        finally:
            self.s.timeout = old_to
        # Firmware meldet "OK <anzahl>" oder "TIMEOUT bei Byte <n>"
        if resp.startswith("TIMEOUT"):
            raise IOError(
                f"Firmware bekam nicht alle Bytes: {resp}. "
                f"Pruefe uC-Reset und WP-Pin.")
        if not resp.startswith("OK"):
            raise IOError(f"Schreiben nicht bestaetigt (bekam: {resp!r})")

        # Verify: komplett zuruecklesen und vergleichen
        readback = self.read_dump(size, page, addrbytes)
        if readback != data:
            # erste Abweichung finden fuer eine hilfreiche Meldung
            for i in range(size):
                if readback[i] != data[i]:
                    raise IOError(
                        f"Verify fehlgeschlagen ab Adresse 0x{i:02X}: "
                        f"geschrieben 0x{data[i]:02X}, "
                        f"gelesen 0x{readback[i]:02X}")
            raise IOError("Verify fehlgeschlagen (Laengen-Differenz)")
        return f"{resp} - verifiziert OK"


def hexdump(data, width=16, limit=4096):
    out = []
    n = min(len(data), limit)
    for off in range(0, n, width):
        chunk = data[off:off + width]
        hexs = " ".join(f"{b:02X}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"{off:06X}  {hexs:<{width*3}}  {text}")
    if len(data) > limit:
        out.append(f"... ({len(data)-limit} weitere Bytes ausgeblendet)")
    return "\n".join(out)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("24C EEPROM Tool")
        self.geometry("760x620")
        self.ee = None
        self.data = b""
        self._build()
        self.refresh_ports()

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Port:").grid(row=0, column=0, sticky="w")
        self.port_cb = ttk.Combobox(top, width=22, state="readonly")
        self.port_cb.grid(row=0, column=1, padx=4)
        ttk.Button(top, text="↻", width=3,
                   command=self.refresh_ports).grid(row=0, column=2)
        self.conn_btn = ttk.Button(top, text="Verbinden",
                                   command=self.toggle_conn)
        self.conn_btn.grid(row=0, column=3, padx=4)

        ttk.Label(top, text="Chip:").grid(row=0, column=4, padx=(16, 2))
        self.chip_cb = ttk.Combobox(top, width=10, state="readonly",
                                    values=list(CHIPS.keys()))
        self.chip_cb.set("24C02")
        self.chip_cb.grid(row=0, column=5)
        ttk.Button(top, text="Auto-Erkennen",
                   command=self.do_autodetect).grid(row=0, column=6, padx=6)

        btns = ttk.Frame(self, padding=(8, 0))
        btns.pack(fill="x")
        self.read_btn = ttk.Button(btns, text="Auslesen → Datei",
                                   command=self.do_read, state="disabled")
        self.read_btn.pack(side="left", padx=2)
        self.write_btn = ttk.Button(btns, text="Datei → Schreiben",
                                    command=self.do_write, state="disabled")
        self.write_btn.pack(side="left", padx=2)
        self.load_btn = ttk.Button(btns, text="bin laden",
                                   command=self.do_load)
        self.load_btn.pack(side="left", padx=2)

        self.prog = ttk.Progressbar(self, mode="indeterminate")
        self.prog.pack(fill="x", padx=8, pady=4)

        ttk.Label(self, text="Hex-Vorschau:").pack(anchor="w", padx=8)
        self.hex = scrolledtext.ScrolledText(self, height=18,
                                             font=("Courier New", 9))
        self.hex.pack(fill="both", expand=True, padx=8, pady=2)

        ttk.Label(self, text="Log:").pack(anchor="w", padx=8)
        self.logbox = scrolledtext.ScrolledText(self, height=7,
                                                font=("Courier New", 9))
        self.logbox.pack(fill="x", padx=8, pady=(0, 8))

    # ---------- Helpers ----------
    def log(self, msg):
        self.logbox.insert("end", str(msg) + "\n")
        self.logbox.see("end")
        self.update_idletasks()

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb["values"] = ports
        if ports and not self.port_cb.get():
            self.port_cb.set(ports[0])

    def chip_params(self):
        name = self.chip_cb.get()
        size, page, ab = CHIPS[name]
        return name, size, page, ab

    def _run_bg(self, fn):
        """Laeuft Aktion im Thread, sperrt Buttons, dreht Progressbar."""
        def wrap():
            self.prog.start(12)
            try:
                fn()
            except Exception as e:
                self.log(f"FEHLER: {e}")
                messagebox.showerror("Fehler", str(e))
            finally:
                self.prog.stop()
        threading.Thread(target=wrap, daemon=True).start()

    # ---------- Actions ----------
    def toggle_conn(self):
        if self.ee:
            self.ee.close()
            self.ee = None
            self.conn_btn.config(text="Verbinden")
            self.read_btn.config(state="disabled")
            self.write_btn.config(state="disabled")
            self.log("Getrennt.")
            return
        port = self.port_cb.get()
        if not port:
            messagebox.showwarning("Port", "Kein Port gewaehlt.")
            return
        try:
            self.ee = EEPROM(port, log=self.log)
            self.conn_btn.config(text="Trennen")
            self.read_btn.config(state="normal")
            self.write_btn.config(state="normal")
            self.log(f"Verbunden mit {port}.")
        except Exception as e:
            messagebox.showerror("Verbindung", str(e))

    def do_autodetect(self):
        if not self.ee:
            messagebox.showwarning("Nicht verbunden", "Erst verbinden.")
            return
        def task():
            res = self.ee.autodetect()
            if res:
                self.chip_cb.set(res[0])
        self._run_bg(task)

    def do_read(self):
        if not self.ee:
            return
        name, size, page, ab = self.chip_params()
        path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            initialfile=f"{name}_dump.bin",
            filetypes=[("Binary", "*.bin"), ("Alle", "*.*")])
        if not path:
            return
        def task():
            self.log(f"Lese {name} ({size} Bytes) ...")
            data = self.ee.read_dump(size, page, ab)
            with open(path, "wb") as f:
                f.write(data)
            self.data = data
            self.hex.delete("1.0", "end")
            self.hex.insert("1.0", hexdump(data))
            self.log(f"Fertig: {size} Bytes -> {path}")
        self._run_bg(task)

    def do_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("Binary", "*.bin"), ("Alle", "*.*")])
        if not path:
            return
        with open(path, "rb") as f:
            self.data = f.read()
        self.hex.delete("1.0", "end")
        self.hex.insert("1.0", hexdump(self.data))
        self.log(f"Geladen: {len(self.data)} Bytes aus {path}")

    def do_write(self):
        if not self.ee:
            return
        if not self.data:
            messagebox.showwarning("Keine Daten",
                                   "Erst eine bin-Datei laden oder auslesen.")
            return
        name, size, page, ab = self.chip_params()
        if len(self.data) != size:
            if not messagebox.askyesno(
                    "Groesse",
                    f"Daten sind {len(self.data)} Bytes, {name} erwartet "
                    f"{size}. Trotzdem fortfahren ist nicht moeglich.\n\n"
                    f"Anderen Chip waehlen?"):
                return
            return
        if not messagebox.askyesno("Schreiben bestaetigen",
                                   f"{name} wird ueberschrieben. Fortfahren?"):
            return
        def task():
            self.log(f"Schreibe {size} Bytes auf {name} ...")
            resp = self.ee.write_dump(self.data, size, page, ab)
            self.log(f"Antwort: {resp}")
        self._run_bg(task)


if __name__ == "__main__":
    App().mainloop()

