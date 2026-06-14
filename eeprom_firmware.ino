#include <Wire.h>

// =====================================================================
//  24C EEPROM Tool - Firmware fuer Arduino UNO / Nano (ATmega328P)
//  Befehle ueber Serial (115200 Baud):
//    I            -> Info (aktuelle Konfig)
//    S s p a\n    -> Set: Groesse, Pagesize, Adressbytes(1/2)
//    D            -> Detect: erkennt Adressbreite + Groesse hardwarenah
//    R            -> Read: gibt EE_SIZE Rohbytes aus
//    W            -> Write: erwartet EE_SIZE Bytes, schreibt sie
// =====================================================================

const byte I2C_ADDR = 0x50;   // Basis-Adresse (A0..A2 = GND)
uint32_t EE_SIZE  = 256;
byte     PAGE_SIZE = 8;
bool     ADDR16   = false;

void setup() {
  Wire.begin();
  Wire.setClock(100000);   // 100 kHz Standard. Bei sauberem Bus (uC im
                           // Reset) stabil. Bei Problemen auf 50000 senken.
  Serial.begin(115200);
  while (!Serial);
}

byte devAddr(uint32_t a) {
  if (ADDR16) return I2C_ADDR;
  return I2C_ADDR | ((a >> 8) & 0x07);
}

void sendAddr(uint32_t a) {
  if (ADDR16) Wire.write((byte)(a >> 8));
  Wire.write((byte)(a & 0xFF));
}

// Roh-Lesung eines Bytes (ein einzelner I2C-Zugriff)
byte readByteRaw(uint32_t a) {
  Wire.beginTransmission(devAddr(a));
  sendAddr(a);
  Wire.endTransmission();
  Wire.requestFrom((int)devAddr(a), 1);
  if (Wire.available()) return Wire.read();
  return 0xFF;
}

// Verifizierte Lesung: liest mehrfach und nimmt den Wert erst, wenn
// zwei aufeinanderfolgende Lesungen uebereinstimmen. Faengt sporadische
// Bitfehler auf grenzwertigem Bus ab.
byte readByte(uint32_t a) {
  readByteRaw(a);          // Dummy-Read: initialisiert Adresszeiger/Bus,
                           // stabilisiert den ersten Zugriff einer Sequenz
  byte last = readByteRaw(a);
  for (byte tries = 0; tries < 6; tries++) {
    byte v = readByteRaw(a);
    if (v == last) return v;   // zwei gleiche Lesungen -> vertrauenswuerdig
    last = v;
  }
  return last;
}

void writeByte(uint32_t a, byte v) {
  Wire.beginTransmission(devAddr(a));
  sendAddr(a);
  Wire.write(v);
  Wire.endTransmission();
  delay(6);
}

// --- generisches Lesen/Schreiben mit explizitem Adressmodus (Detect) ---
byte readByteMode(uint32_t a, bool addr16) {
  byte dev = addr16 ? I2C_ADDR : (I2C_ADDR | ((a >> 8) & 0x07));
  Wire.beginTransmission(dev);
  if (addr16) Wire.write((byte)(a >> 8));
  Wire.write((byte)(a & 0xFF));
  Wire.endTransmission();   // Stop - wie im funktionierenden Scanner
  Wire.requestFrom((int)dev, 1);
  if (Wire.available()) return Wire.read();
  return 0xFF;
}

void writeByteMode(uint32_t a, byte v, bool addr16) {
  byte dev = addr16 ? I2C_ADDR : (I2C_ADDR | ((a >> 8) & 0x07));
  Wire.beginTransmission(dev);
  if (addr16) Wire.write((byte)(a >> 8));
  Wire.write((byte)(a & 0xFF));
  Wire.write(v);
  Wire.endTransmission();
  delay(6);
}

// --- Erkennung der Adressbreite ---
// Kleine Chips (<=24C16) nehmen 1 Adressbyte. Schickt man 2 Bytes,
// landet das Datenbyte als zweites "Adressbyte" -> Lesen liefert Murks.
// Wir vergleichen Byte0 in beiden Modi ueber mehrere Adressen.
bool detectAddr16() {
  byte testAddrs[] = {0x00, 0x01, 0x10};
  byte mism = 0;
  for (byte i = 0; i < 3; i++) {
    byte v1 = readByteMode(testAddrs[i], false);
    byte v2 = readByteMode(testAddrs[i], true);
    if (v1 != v2) mism++;
  }
  // Stimmen die Modi durchweg ueberein, ist 2-Byte-Adressierung plausibel.
  return (mism == 0);
}

// --- Groesse per zerstoerungsfreiem Wrap-Around-Test ---
uint32_t detectSize(bool addr16) {
  byte orig0 = readByteMode(0, addr16);
  byte probe = orig0 ^ 0xFF;
  writeByteMode(0, probe, addr16);

  uint32_t sizes1[] = {128, 256, 512, 1024, 2048};
  uint32_t sizes2[] = {4096, 8192, 16384, 32768, 65536};
  uint32_t* sizes = addr16 ? sizes2 : sizes1;
  byte n = 5;

  uint32_t result = addr16 ? 65536 : 2048;
  for (byte i = 0; i < n; i++) {
    uint32_t sz = sizes[i];
    byte origS = readByteMode(sz, addr16);
    byte markS = orig0;
    writeByteMode(sz, markS, addr16);
    byte check0 = readByteMode(0, addr16);
    writeByteMode(sz, origS, addr16);
    if (check0 == markS && markS != probe) {
      result = sz;
      break;
    }
  }
  writeByteMode(0, orig0, addr16);
  return result;
}

byte pageFor(uint32_t size) {
  if (size <= 256)   return 8;
  if (size <= 2048)  return 16;
  if (size <= 8192)  return 32;
  return 64;
}

void loop() {
  if (!Serial.available()) return;
  char cmd = Serial.read();

  if (cmd == 'I') {
    Serial.print(F("EEPROM ")); Serial.print(EE_SIZE);
    Serial.print(' '); Serial.print(PAGE_SIZE);
    Serial.print(' '); Serial.println(ADDR16 ? 2 : 1);
  }
  else if (cmd == 'S') {
    // Komplette Zeile bis '\n' einlesen, dann sauber parsen.
    // Vermeidet das gierige Timeout-Verhalten von parseInt(), das
    // nachfolgende Kommandos/Daten verschlucken konnte.
    char buf[24];
    byte i = 0;
    unsigned long t0 = millis();
    while (i < sizeof(buf) - 1) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') break;
        buf[i++] = c;
      } else if (millis() - t0 > 1000) {
        break;   // Timeout-Schutz
      }
    }
    buf[i] = '\0';
    long s = 0, p = 0, ab = 0;
    sscanf(buf, " %ld %ld %ld", &s, &p, &ab);
    if (s > 0) EE_SIZE = s;
    if (p > 0) PAGE_SIZE = p;
    ADDR16 = (ab == 2);
    Serial.println(F("SET"));
  }
  else if (cmd == 'D') {
    bool a16 = detectAddr16();
    uint32_t sz = detectSize(a16);
    EE_SIZE = sz;
    ADDR16 = a16;
    PAGE_SIZE = pageFor(sz);
    Serial.print(F("DETECT size=")); Serial.print(sz);
    Serial.print(F(" addrbytes=")); Serial.print(a16 ? 2 : 1);
    Serial.print(F(" page=")); Serial.println(PAGE_SIZE);
  }
  else if (cmd == 'H') {
    // Diagnose: ersten paar Bytes als lesbaren Hex-Text ausgeben
    Serial.print(F("HEX"));
    for (uint32_t a = 0; a < 8 && a < EE_SIZE; a++) {
      byte v = readByte(a);
      Serial.print(' ');
      if (v < 0x10) Serial.print('0');
      Serial.print(v, HEX);
    }
    Serial.println();
  }
  else if (cmd == 'T') {
    // Selbsttest: Muster an Adresse 0..7 schreiben und zuruecklesen
    Serial.print(F("TEST schreibe "));
    for (byte i = 0; i < 8; i++) {
      writeByte(i, 0xA0 + i);     // 0xA0,0xA1,...0xA7
      Serial.print(0xA0 + i, HEX); Serial.print(' ');
    }
    Serial.print(F("| lese zurueck "));
    bool ok = true;
    for (byte i = 0; i < 8; i++) {
      byte v = readByte(i);
      if (v < 0x10) Serial.print('0');
      Serial.print(v, HEX); Serial.print(' ');
      if (v != (0xA0 + i)) ok = false;
    }
    Serial.println(ok ? F("=> OK") : F("=> FEHLER"));
  }
  else if (cmd == 'R') {
    for (uint32_t a = 0; a < EE_SIZE; a++) Serial.write(readByte(a));
  }
  else if (cmd == 'W') {
    // Flussgesteuertes Schreiben in 32-Byte-Bloecken. Nach jedem Block
    // sendet die Firmware ein '.' als Quittung; die GUI sendet erst dann
    // den naechsten Block. Das verhindert Pufferueberlauf, denn jedes
    // writeByte() hat ein Schreibdelay, waehrenddessen sonst weitere
    // Bytes den 64-Byte-Seriellpuffer ueberfluten wuerden.
    const byte BLOCK = 32;
    while (Serial.available()) Serial.read();
    Serial.println(F("READY"));
    uint32_t a = 0;
    bool timeout = false;
    while (a < EE_SIZE) {
      byte want = (EE_SIZE - a) < BLOCK ? (EE_SIZE - a) : BLOCK;
      for (byte i = 0; i < want; i++) {
        unsigned long t0 = millis();
        while (!Serial.available()) {
          if (millis() - t0 > 3000) { timeout = true; break; }
        }
        if (timeout) break;
        writeByte(a, Serial.read());
        a++;
      }
      if (timeout) break;
      Serial.write('.');   // Block-Quittung: GUI darf naechsten Block senden
    }
    if (timeout) {
      Serial.print(F("TIMEOUT bei Byte ")); Serial.println(a);
    } else {
      Serial.print(F("OK ")); Serial.println(a);
    }
  }
}
