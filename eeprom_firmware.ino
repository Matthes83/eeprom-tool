#include <Wire.h>

// ====== KONFIG ======
const byte I2C_ADDR = 0x50;   // A0..A2 = GND
// Diese Werte sind nur Default/Fallback. Per Serial-Befehl 'S' werden
// Groesse/Pagesize/Adressbreite zur Laufzeit gesetzt (von der GUI).
uint32_t EE_SIZE = 256;
byte     PAGE_SIZE = 8;
bool     ADDR16 = false;
// =====================

void setup() {
  Wire.begin();
  Wire.setClock(100000);
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

byte readByte(uint32_t a) {
  Wire.beginTransmission(devAddr(a));
  sendAddr(a);
  Wire.endTransmission();
  Wire.requestFrom((int)devAddr(a), 1);
  return Wire.read();
}

void writeByte(uint32_t a, byte v) {
  Wire.beginTransmission(devAddr(a));
  sendAddr(a);
  Wire.write(v);
  Wire.endTransmission();
  delay(6);
}

// ----- Probe: liest ein Byte an Adresse a unter Annahme einer Adressbreite -----
// addrMode: 1 = ein Adressbyte (mit Bank-Bits in Geraeteadresse), 2 = zwei Adressbytes
byte probeRead(uint32_t a, byte addrMode) {
  byte dev, hi;
  if (addrMode == 2) {
    dev = I2C_ADDR;
    Wire.beginTransmission(dev);
    Wire.write((byte)(a >> 8));
    Wire.write((byte)(a & 0xFF));
  } else {
    dev = I2C_ADDR | ((a >> 8) & 0x07);
    Wire.beginTransmission(dev);
    Wire.write((byte)(a & 0xFF));
  }
  Wire.endTransmission();
  Wire.requestFrom((int)dev, 1);
  if (Wire.available()) return Wire.read();
  return 0xFF;
}

// Prueft, ob an I2C-Adresse ein ACK kommt
bool ackAt(byte dev) {
  Wire.beginTransmission(dev);
  return Wire.endTransmission() == 0;
}

void loop() {
  if (!Serial.available()) return;
  char cmd = Serial.read();

  if (cmd == 'I') {
    Serial.print("EEPROM "); Serial.print(EE_SIZE);
    Serial.print(" "); Serial.print(PAGE_SIZE);
    Serial.print(" "); Serial.println(ADDR16 ? 2 : 1);
  }
  else if (cmd == 'S') {            // Set: "S <size> <page> <addrbytes>\n"
    EE_SIZE   = Serial.parseInt();
    PAGE_SIZE = Serial.parseInt();
    ADDR16    = (Serial.parseInt() == 2);
    while (Serial.available() && Serial.peek() != '\n') Serial.read();
    if (Serial.peek() == '\n') Serial.read();
    Serial.println("SET");
  }
  else if (cmd == 'P') {           // Probe / Autodetect
    // 1) Welche I2C-Bank-Adressen antworten? (unterscheidet kleine Chips)
    byte banks = 0;
    for (byte b = 0; b < 8; b++) if (ackAt(I2C_ADDR | b)) banks |= (1 << b);

    // 2) Wrap-Around-Test fuer beide Adressmodi.
    // Wir sichern Byte@0, schreiben Marker, lesen an Kandidaten-Endadressen.
    // Achtung: zerstoerungsfrei nur soweit moeglich -> wir testen lesend
    // ueber Bank-Verhalten + 2-Byte-Adress-ACK.

    // Test ob 2-Adressbyte-Zugriff plausibel: lese @0 zweimal in beiden Modi
    byte r1a = probeRead(0, 1);
    byte r1b = probeRead(0, 2);

    Serial.print("PROBE banks=0x");
    Serial.print(banks, HEX);
    Serial.print(" a1@0="); Serial.print(r1a);
    Serial.print(" a2@0="); Serial.print(r1b);
    Serial.println();
  }
  else if (cmd == 'R') {
    for (uint32_t a = 0; a < EE_SIZE; a++) Serial.write(readByte(a));
  }
  else if (cmd == 'W') {
    uint32_t a = 0;
    while (a < EE_SIZE) {
      while (!Serial.available());
      writeByte(a, Serial.read());
      a++;
    }
    Serial.println("OK");
  }
}
