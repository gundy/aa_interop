# 06 — Data Dictionary (Enums)

Normative wire values for register payloads and XML responses. Values outside
the listed ranges are rejected by the reference implementation.

## 6.1 System mode (register 05 byte 1, XML `mode`)

| Value | Name |
|---|---|
| 1 | cool |
| 2 | heat |
| 3 | vent |
| 4 | auto |
| 5 | dry |
| 6 | myauto (tablet-only; never transmitted by the CB) |

## 6.2 Fan speed (register 05 byte 2, XML `fanSpeed`)

| Value | Name |
|---|---|
| 0 | off |
| 1 | low |
| 2 | medium |
| 3 | high |
| 4 | auto |
| 5 | autoAA |

## 6.3 System state (register 05 byte 0, XML `airconOnOff`)

| Value | Name |
|---|---|
| 0 | off |
| 1 | on |

## 6.4 Zone state (register 03 byte 1 bit 7, XML `setting`)

| Value | Name |
|---|---|
| 0 | closed |
| 1 | open |

## 6.5 Sensor type (register 03 byte 2)

| Value | Name |
|---|---|
| 0 | no sensor |
| 1 | RF |
| 2 | wired |
| 3 | RF2CAN booster |
| 4 | RF_X |

## 6.6 Zone type (zone XML `hasClimateControl`)

| Value | Name | Behaviour |
|---|---|---|
| 0 | percent | damper controlled by `value` |
| 1 | temperature | zone controlled by `setTemp` |

## 6.7 Motion status (register 04 byte 3, XML `motionCurrentState`)

| Value | Name |
|---|---|
| 0 | no sensor |
| 1 | motion disabled (user) |
| 2 | motion enabled |
| 21 | motion stage 1 |
| 22 | motion stage 2 |

Motion config (register 04 byte 4) is 0–2.

## 6.8 Fresh air status (register 05 byte 5, XML `FAstatus`)

| Value | Name |
|---|---|
| 0 | none |
| 1 | off |
| 2 | on |

## 6.9 Activation status (register 02 byte 1, XML `activationCodeStatus`)

| Value | Name |
|---|---|
| 0 | no code |
| 1 | code enabled |
| 2 | expired |

## 6.10 Aircon unit type (register 02 byte 0, XML `zoneStationHasUnitControl`)

| Value | Name |
|---|---|
| 0x11 | Daikin |
| 0x12 | Panasonic |
| 0x13 | Fujitsu |
| 0x19 | Samsung DVM |

## 6.11 CB type (register 06 byte 2, XML `cbType`)

| Value | Meaning |
|---|---|
| 0 | unknown / unset |
| 3 | aircon-only CB |
| 4 | split-type system (RF-connected; unit type `08` on the bus) |
| 5 | split-type system; announces new RF devices |

## 6.12 Zone error flags (register 04 byte 5)

Composed bit flags (tablet-side):

| Bit | Meaning |
|---|---|
| 0 | temperature-sensor clash |
| 1 | low battery |
| 2 | motion / other clash |

## 6.13 RF device types (register 26 byte 1)

| Value | Meaning |
|---|---|
| 129, 130 | device reported with unit type `07` |
| other | device reported with unit type `08` |

## 6.14 Error codes (register 08 / XML `airConErrorCode`)

CB-originated (may appear on the bus):

| Code | Meaning |
|---|---|
| AA1 | Communication error between CB componentry and AC unit |
| AA2 | Multiple unit controllers detected |
| AA3 | Communication error |
| AA4 | System is not detecting any temperature sensors |
| AA81 | Wall sensor detected but not allocated to exactly one zone |
| AA82 | Wall sensor detected but not allocated to exactly one zone |
| AA83 | Wall sensor detected but not allocated to exactly one zone |
| AA86 | Wireless wall sensor low battery |
| AA89 | Multiple sensors detected on the same zone |

Tablet-generated diagnostics (never on the bus; surfaced in the UI):

| Code | Meaning |
|---|---|
| AA60 | VAMS system not set up correctly |
| AA62 | VAMS-RAS not plugged into CB RAS port |
| AA63 | VAMS-SAS not plugged into CB SAS port |
| AA64 | Temperature sensor allocated to zone 1 (VAMS) |
| AA65 | Temperature sensor allocated to zone 2 (VAMS) |
| AA123–AA127 | TSP errors |
