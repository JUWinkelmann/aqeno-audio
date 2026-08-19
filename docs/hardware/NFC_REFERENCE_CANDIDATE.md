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


## Object area requirement (ADR 0026 § 11)

Decided before any reader is chosen, because it constrains both the antenna and the enclosure:

> **Place, do not aim.**

- a **generous, flat object area** — **no recess, no well**. Standing figures work, simple
  3D-printed objects need no AQENO-specific under-geometry, and flat cards work equally;
- error-tolerant across the whole area rather than at one sweet spot;
- findable by touch where that is possible without intrusive geometry — a slight material or texture
  difference, or a constructional seam, may be evaluated;
- the enclosure reserves adequate area from the start; the antenna solution remains a measurement
  and is not implied by this requirement;
- **magnetic positioning** may be added later as an option. NFC identifies; magnetism may position
  and hold. Never a precondition, never mandatory proprietary geometry, ordinary cards and tags must
  keep working, and interaction with the antenna, speakers, display and remaining electronics must
  be measured. No magnet arrangement is specified.

Read range must therefore be validated over the intended area with a card and with a standing
object, not only at the antenna centre.
