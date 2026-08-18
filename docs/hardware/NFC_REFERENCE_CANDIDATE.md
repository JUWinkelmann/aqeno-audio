# RH1 NFC reader candidate

**Status:** Candidate for acquisition and hardware spike; not yet Reference-supported.

RH1 currently has no NFC reader. The smallest evidence-driven next step is one **Adafruit PN532
NFC/RFID Controller Breakout v1.6 (Product 364)** connected over **SPI**, plus appropriate female
jumper leads or a deliberately made harness.

Why this candidate:

- PN532 reads ISO/IEC 14443A/MIFARE-compatible 13.56 MHz tags, matching AQENO's brand-neutral UID
  trigger model ([NXP PN532 data sheet](https://www.nxp.com/docs/en/nxp/data-sheets/PN532_C1.pdf)).
- Adafruit documents Python/CircuitPython support on Raspberry Pi.
- Adafruit explicitly recommends SPI rather than I²C on Raspberry Pi; its I²C route needs additional
  request/reset wiring to avoid clock-stretching problems
  ([Adafruit wiring guide](https://learn.adafruit.com/adafruit-pn532-rfid-nfc?view=all),
  [Python guide](https://learn.adafruit.com/adafruit-pn532-rfid-nfc/python-circuitpython)).
- SPI keeps NFC off RH1's existing Qwiic/I²C chain. The current controls remain on GPIO 2/3,
  MiniAmp I²S audio uses its own pins, and the DSI display remains independent.

This is not a no-solder Qwiic module. Do not buy an unrelated I²C RFID EEPROM board: a tag/EEPROM
device is not a reader. Before promoting PN532 to Reference, the spike must prove reliable UID reads,
repeated presentation/removal, boot recovery, coexistence with audio/controls, enclosure read range
and clean failure when disconnected.

Not required for the spike: proprietary tag content extraction, MIFARE key handling, payment/card
emulation, writing tags or treating a third-party object as permission. AQENO stores only the local
assignment from observed UID to AQENO target.
