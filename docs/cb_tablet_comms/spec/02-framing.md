# 02 — Framing

## 2.1 Frame envelope

Every message on the bus is wrapped in an XML-like envelope:

```
<U>{PAYLOAD}</U={CRC}>
```

- `{PAYLOAD}` — the message payload bytes (see §2.3).
- `{CRC}` — two lowercase hex digits: CRC-8 of the payload bytes only.

Frames in a CB burst are separated by a single ASCII space (`0x20`). A burst may
contain several frames, e.g. `Ping` followed by a `getCAN` reply.

## 2.2 CRC-8

| Parameter | Value |
|---|---|
| Width | 8 |
| Polynomial | `0xB2` (x⁸ + x⁷ + x⁵ + x⁴ + x) |
| Initial value | `0x00` |
| Final XOR | `0xFF` |
| Reflection | reflected (right-shift) |

Reference implementation:

```c
uint8_t CRC8(const uint8_t *data, int length)
{
   uint8_t crc = 0x00;
   for(int i=0; i<length; i++) {
      crc ^= *data++;
      for (int j=0; j<8; j++) {
          if ((crc & 0x01) > 0) {
              crc = (crc >> 1) ^ 0xB2;
          } else {
              crc >>= 1;
          }
      }
   }
   return crc ^ 0xff;
}
```

Golden values:

| Payload | CRC |
|---|---|
| `Ping` | `db` |
| `setCAN ` | `b2` |
| `ackCAN 1` | `aa` |
| `getSystemData` | `15` |

## 2.3 Payload classes

| Payload class | Example | Direction | Purpose |
|---|---|---|---|
| `Ping` | `Ping` | CB → tablet | Bus keepalive; grants the tablet one reply slot |
| Poll request | `getSystemData` | tablet → CB | Legacy channel (§05); may go unanswered on modern CBs |
| Register write | `setCAN <records…>` | tablet → CB | Write one or more register records |
| Register read reply | `getCAN <n> <records…>` | CB → tablet | Deliver register records; `n` = 1 (ok) or 0 (nack) |
| Acknowledge | `ackCAN 0|1` | tablet → CB | Acknowledge a `getCAN` (1 = CRC ok, 0 = retry) |
| Command | `setSystemData?mode=1` | tablet → CB | Legacy channel (§05); may be ignored |
| XML response | `<request>getSystemData</request>…` | CB → tablet | Legacy channel (§05); only produced by CBs that implement it |

The tablet transmits at most one framed payload per `Ping`.

## 2.4 CAN2 register record format

Register records are fixed-width, 25 hexadecimal characters, no spaces:

```
TT DD UUUUU RR DDDDDDDDDDDDDD
```

| Field | Chars | Width | Meaning |
|---|---|---|---|
| `TT` | 0–1 | 2 hex | Unit type (see §2.5) |
| `DD` | 2–3 | 2 hex | Destination / direction byte |
| `UUUUU` | 4–8 | 5 hex | 20-bit unit identifier (lowercase) |
| `RR` | 9–10 | 2 hex | Register identifier |
| `DDDDDDDDDDDDDD` | 11–24 | 7 bytes | Register payload |

Example:

```
setCAN 0701abcde1201234501000000
```

breaks down as: unit type `07` (air conditioning), destination `01` (Control
Box), unit id `abcde`, register `12` (sensor pairing), payload
`01234501000000` (attach sensor `012345` to zone `01`).

## 2.5 Unit types

| `TT` | Meaning |
|---|---|
| `02` | Lights |
| `07` | Air conditioning — wired connection |
| `08` | Air conditioning — RF-connected (split systems), and RF devices |

A CB of type "split system" presents itself with unit type `08` for both its
register reads and writes. Implementations must accept `07` and `08` when
filtering air-conditioning traffic, and must preserve the unit type of a CB
when writing records back to it (a split system CB must be written with `08`).

## 2.6 Destination byte

| `DD` | Meaning |
|---|---|
| `01` | Destined for the Control Box |
| `03` | Destined for the tablet |
| `04` | Observed on CB→tablet traffic; meaning unverified |

`03` and `04` are both accepted on inbound traffic.
