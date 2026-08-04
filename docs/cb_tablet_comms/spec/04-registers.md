# 04 — Register Catalog

This document is the normative reference for CAN2 register records. Payloads
are 7 bytes (14 hex chars). The JZ identifiers are the CB message names used
in firmware/service documentation; several registers carry different payload
meaning depending on direction, noted per register.

Byte positions within a record: `TT DD UUUUU RR` = chars 0–10, payload bytes
at chars 11, 13, 15, 17, 19, 21, 23 (2 hex chars each).

Validation ranges shown are the bounds accepted by the reference tablet
implementation; records outside these ranges are rejected.

---

## 01 — Zone configuration (JZ6 write / JZ7 read)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Header | — | Direction-dependent header byte (e.g. `0x11` tablet→CB, `0x20` CB→tablet) |
| 1 | Number of zones | 0–10 | |
| 2 | Number of constant zones | 0–3 | |
| 3 | Constant zone 1 | 0–10 | 0 = disabled |
| 4 | Constant zone 2 | 0–10 | |
| 5 | Constant zone 3 | 0–10 | |
| 6 | Filter clean | 0/1 | 1 = filter clean required |

On write the tablet sends its current zone configuration; on read the CB
announces its configuration (e.g. after dump or when zones change).

---

## 02 — Unit type / activation status

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Unit type | — | `0x11` Daikin, `0x12` Panasonic, `0x13` Fujitsu, `0x19` Samsung DVM |
| 1 | Activation status | 0–2 | 0 = no code, 1 = code enabled, 2 = expired |
| 2 | Dictionary FW major | — | |
| 3 | Dictionary FW minor | — | |

Note: the activation-status mapping (0 = no code, 1 = code enabled,
2 = expired) supersedes earlier documentation that listed 1 = expired /
2 = code enabled.

---

## 03 — Zone state (JZ11)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Zone number | 1–10 | |
| 1 | Bit 7: open flag; bits 6–0: damper % | 0–100 | 1 = zone open |
| 2 | Sensor type | 0–4 | see `06-enums.md` |
| 3 | Set temperature × 2 | 0–80 | 0–40 °C |
| 4 | Measured temperature, integer part | — | |
| 5 | Measured temperature, decimal part | 0–9 | |
| 6 | Reserved | — | written as 0 |

On **write** the sensor-type byte is sent as `00`; the CB populates it after a
sensor is attached. Measured temperature is populated only after the tablet
has paired a sensor to the zone (register 12).

---

## 04 — Zone configuration (JZ13)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Zone number | 1–10 | |
| 1 | Min damper | — | |
| 2 | Max damper | — | |
| 3 | Motion status | 0–22 | see `06-enums.md` |
| 4 | Motion config | 0–2 | |
| 5 | Zone error | — | bit flags, see below |
| 6 | CB RSSI | — | |

Zone error bit flags (tablet-side composition): bit 0 = temperature-sensor
clash, bit 1 = low battery, bit 2 = motion/other clash.

---

## 05 — System status (JZ5 write / JZ14–JZ15 read)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | System state | 0–1 | 0 = off, 1 = on |
| 1 | System mode | 0–5 | see `06-enums.md`; the CB never transmits 6 |
| 2 | System fan | 0–5 | see `06-enums.md` |
| 3 | Set temperature × 2 | 0–80 | 0–40 °C |
| 4 | MyZone id | 0–10 | 0 = disabled |
| 5 | Fresh air status | 0–2 | 0 = none, 1 = off, 2 = on |
| 6 | RF system id | 0–16 | |

Mode 6 ("my auto") is a tablet-side mode: the tablet may present it in its UI
and synthesise the corresponding writes, but the CB never sends it. Reads of
mode 6 from the CB are treated as auto. The write side is unverified: whether
a register-05 write with mode 6 is accepted by the CB (or normalised/ignored)
has not been observed; implementations should expect no guarantee either way.

---

## 06 — CB firmware / flush (JZ16 write / JZ17 read)

Direction tablet→CB (JZ16, flush):

| Byte | Field |
|---|---|
| 0–6 | all zero |

Unit id is `00000` for the global flush; a unit-scoped flush carries the
target unit's id.

Direction CB→tablet (JZ17, firmware status):

| Byte | Field |
|---|---|
| 0 | CB firmware major |
| 1 | CB firmware minor |
| 2 | CB type (see `06-enums.md`) |
| 3 | RF firmware major |
| 4–6 | zero |

---

## 07 — Firmware acknowledgement (JZ18, tablet→CB)

| Byte | Field |
|---|---|
| 0–6 | all zero |

Sent by the tablet in response to every register-06 (JZ17) firmware
announcement. Unit type and unit id echo the announcement (split-system CBs
announce with type `08` and must be answered with type `08`). The payload is
always all-zero; there is no acknowledged read of this register.

---

## 08 — Aircon error (JZ22, CB→tablet)

| Byte | Field |
|---|---|
| 0–4 | Error code, 5 ASCII characters |
| 5–6 | zero |

The code is space-trimmed; common codes are `AA1` (no communication with the
AC unit), `AA2` (multiple unit controllers), `AA3` (communication error),
`AA4` (no temperature sensors detected). See `07-flows.md` for the full error
table, including tablet-generated diagnostics that never appear on the bus.

---

## 09 — Activation code entry (JZ23, tablet→CB)

| Byte | Field |
|---|---|
| 0 | Action: 1 = set new code, 2 = unlock |
| 1 | Unlock code, high byte |
| 2 | Unlock code, low byte |
| 3 | Activation time (days) |
| 4–6 | zero |

Sent with unit id `00000`.

---

## 0a — Unit announcement (JZ24, CB→tablet)

All-zero payload. Informs the tablet that a unit with the given unit id
exists; the tablet records the id as the system's unit identifier.

---

## 12 — Sensor pairing (JZ32 write / JZ33 read)

Direction CB→tablet (JZ33, pairing notification):

| Byte | Field |
|---|---|
| 0–2 | Sensor UID (3 bytes) |
| 3 | Info byte (bit 6 set = pairing requested) |
| 4 | Sensor major revision |
| 5–6 | zero |

Direction tablet→CB (JZ32, attach sensor to zone):

| Byte | Field |
|---|---|
| 0–2 | Sensor UID (3 bytes), `000000` when unknown |
| 3 | Zone number |
| 4–6 | zero |

The pairing flow is described in `07-flows.md`.

---

## 13 — Info byte (JZ35, CB→tablet)

| Byte | Field |
|---|---|
| 0 | Info byte |
| 1–6 | unverified |

Purpose unverified.

---

## 16, 17, 1d, 1e — Referenced registers

Referenced by tablet firmware but the payload formats are unverified. Likely
related to RAS/SAS (VAMS) air-handler units. Reserved.

---

## 26 — RF device pairing (JZ55, tablet→CB)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Pairing control | — | |
| 1 | RF device type | — | 129/130 select unit type `07`, all others `08` |
| 2 | Zone channel | — | |
| 3–6 | zero | | |

Unit type: `07` when the RF device type is 129 or 130, otherwise `08`.

---

## 27 — RF device calibration (JZ57, tablet→CB)

| Byte | Field | Range | Meaning |
|---|---|---|---|
| 0 | Calibration control | — | |
| 1 | Channel | — | |
| 2 | Up/down position | — | |
| 3–6 | zero | | |

Unit type is `08`. Note the wire order of bytes 1 and 2 is swapped relative to
the logical field order (channel is written first, position second).
